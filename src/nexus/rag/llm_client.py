"""LLM client — backend switch between Ollama (local) and Groq (hosted).

Uses LangChain integrations for both backends, supporting:
- Streaming token generation
- Structured output via Pydantic models
- Single (non-streaming) calls for feature modules
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from nexus.config import LLMBackend, get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from langchain_core.language_models import BaseChatModel

logger = structlog.get_logger(__name__)

_llm_instance: BaseChatModel | None = None


def get_llm() -> BaseChatModel:
    """Get the configured LLM instance (singleton).

    Returns LangChain chat model for either Ollama or Groq backend.
    """
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    settings = get_settings()

    if settings.llm_backend == LLMBackend.OLLAMA:
        from langchain_ollama import ChatOllama

        _llm_instance = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.1,
        )
        logger.info("LLM initialized", backend="ollama", model=settings.ollama_model)
    else:
        from langchain_groq import ChatGroq

        _llm_instance = ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.1,
            max_tokens=1024,
        )
        logger.info("LLM initialized", backend="groq", model=settings.groq_model)

    return _llm_instance


async def stream_tokens(
    messages: list[dict[str, str]],
) -> AsyncGenerator[str, None]:
    """Stream LLM response tokens with retry on transient errors.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.

    Yields:
        Individual token strings.
    """
    llm = get_llm()
    langchain_messages = _to_langchain_messages(messages)

    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            async for chunk in llm.astream(langchain_messages):
                if chunk.content:
                    yield str(chunk.content)
            return
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                import asyncio
                wait = 2 ** attempt * 2  # 2s, 4s
                logger.warning("LLM stream error, retrying", attempt=attempt + 1, error=str(exc))
                await asyncio.sleep(wait)

    raise last_exc  # type: ignore[misc]


async def single_call(
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.0,
) -> str:
    """Non-streaming single LLM call.

    Used for feature modules (contradiction detection, gap analysis, etc.)
    """
    llm = get_llm()

    # Override temperature for deterministic feature calls
    bound_llm = llm.bind(temperature=temperature, max_tokens=max_tokens)
    response = await bound_llm.ainvoke(prompt)
    return str(response.content)


async def structured_call(
    prompt: str,
    output_schema: type[Any],
    max_tokens: int = 512,
) -> Any:
    """LLM call with structured output via Pydantic model.

    Uses LangChain's with_structured_output for reliable JSON parsing.
    """
    llm = get_llm()
    structured_llm = llm.with_structured_output(output_schema)
    response = await structured_llm.ainvoke(prompt)
    return response


def _to_langchain_messages(messages: list[dict[str, str]]) -> list[Any]:
    """Convert simple dicts to LangChain message objects."""
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    type_map = {
        "system": SystemMessage,
        "user": HumanMessage,
        "human": HumanMessage,
        "assistant": AIMessage,
        "ai": AIMessage,
    }

    result = []
    for msg in messages:
        cls = type_map.get(msg["role"], HumanMessage)
        result.append(cls(content=msg["content"]))
    return result
