"""LLM client — backend switch between Ollama, Groq, and Gemini.

Uses LangChain integrations for all backends, supporting:
- Streaming token generation
- Structured output via Pydantic models
- Single (non-streaming) calls for feature modules

Default backend: Gemini 2.0 Flash (best free-tier FR+EN quality).
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

    Returns LangChain chat model for the configured backend.
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

    elif settings.llm_backend == LLMBackend.GEMINI:
        from langchain_google_genai import ChatGoogleGenerativeAI

        _llm_instance = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.1,
            max_output_tokens=2048,
        )
        logger.info("LLM initialized", backend="gemini", model=settings.gemini_model)

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


def reset_llm() -> None:
    """Reset the singleton — used when switching backends at runtime or in tests."""
    global _llm_instance
    _llm_instance = None


async def _iter_with_timeout(aiter, timeout_secs: float):
    """Wrap an async iterator and enforce a per-item wait timeout.

    Raises asyncio.TimeoutError if any single __anext__() call exceeds
    timeout_secs. Prevents indefinite hangs when an LLM API is unreachable.
    """
    import asyncio

    while True:
        try:
            item = await asyncio.wait_for(aiter.__anext__(), timeout=timeout_secs)
        except StopAsyncIteration:
            return
        yield item


async def stream_tokens(
    messages: list[dict[str, str]],
    token_timeout: float = 30.0,
) -> AsyncGenerator[str, None]:
    """Stream LLM response tokens with retry on transient errors.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        token_timeout: Seconds to wait for each token before aborting.

    Yields:
        Individual token strings. Raises if all retries yield empty content.
    """
    import asyncio

    llm = get_llm()
    langchain_messages = _to_langchain_messages(messages)

    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            token_count = 0
            async for chunk in _iter_with_timeout(llm.astream(langchain_messages), token_timeout):
                if chunk.content:
                    token_count += 1
                    yield str(chunk.content)

            if token_count > 0:
                return  # Success — tokens were yielded

            # Stream completed but returned zero content — treat as retriable failure
            logger.warning("LLM stream returned empty content", attempt=attempt + 1)
            if attempt < 2:
                await asyncio.sleep(2 ** attempt * 2)
            else:
                raise RuntimeError("LLM returned empty content after 3 attempts")

        except asyncio.TimeoutError:
            backend = get_settings().llm_backend.value
            raise RuntimeError(
                f"LLM backend '{backend}' timed out after {token_timeout:.0f}s waiting for tokens. "
                "Check that the API key is set and the endpoint is reachable."
            ) from None

        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                wait = 2**attempt * 2  # 2s, 4s
                logger.warning("LLM stream error, retrying", attempt=attempt + 1, error=str(exc))
                await asyncio.sleep(wait)

    raise last_exc or RuntimeError("LLM stream failed after 3 attempts")


async def single_call(
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.0,
    call_timeout: float = 30.0,
) -> str:
    """Non-streaming single LLM call.

    Used for feature modules (contradiction detection, gap analysis, etc.)
    """
    import asyncio

    llm = get_llm()
    settings = get_settings()

    # Gemini uses max_output_tokens; other backends use max_tokens
    if settings.llm_backend == LLMBackend.GEMINI:
        bound_llm = llm.bind(temperature=temperature, max_output_tokens=max_tokens)
    else:
        bound_llm = llm.bind(temperature=temperature, max_tokens=max_tokens)

    try:
        response = await asyncio.wait_for(bound_llm.ainvoke(prompt), timeout=call_timeout)
    except asyncio.TimeoutError:
        backend = settings.llm_backend.value
        raise RuntimeError(
            f"LLM backend '{backend}' timed out after {call_timeout:.0f}s. "
            "Check that the API key is set and the endpoint is reachable."
        ) from None
    return str(response.content)


async def structured_call(
    prompt: str,
    output_schema: type[Any],
    max_tokens: int = 512,
    call_timeout: float = 30.0,
) -> Any:
    """LLM call with structured output via Pydantic model.

    Uses LangChain's with_structured_output for reliable JSON parsing.
    """
    import asyncio

    llm = get_llm()
    structured_llm = llm.with_structured_output(output_schema)
    try:
        response = await asyncio.wait_for(structured_llm.ainvoke(prompt), timeout=call_timeout)
    except asyncio.TimeoutError:
        backend = get_settings().llm_backend.value
        raise RuntimeError(
            f"LLM backend '{backend}' structured call timed out after {call_timeout:.0f}s."
        ) from None
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
