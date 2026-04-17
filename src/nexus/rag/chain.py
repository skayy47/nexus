"""LCEL chain — retrieve → format context → generate → extract citations.

This is the core RAG pipeline using LangChain Expression Language (LCEL),
not legacy chains.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from nexus.index.hybrid_retriever import RetrievedChunk

logger = structlog.get_logger(__name__)

# Load the versioned system prompt at module level
_PROMPT_DIR = Path(__file__).parent / "prompts"
_SYSTEM_PROMPT_PATH = _PROMPT_DIR / "system_v1.md"


def _load_system_prompt() -> str:
    """Load the system prompt from the versioned .md file."""
    if _SYSTEM_PROMPT_PATH.exists():
        content = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        # Strip YAML front matter at the end (after ---)
        parts = content.split("---")
        if len(parts) >= 2:
            # Return everything before the last --- block (the metadata)
            return "---".join(parts[:-1]).strip()
        return content.strip()
    # Fallback if file missing
    return (
        "You are NEXUS, an institutional memory engine. "
        "Answer questions based on the provided documents only. "
        "Cite sources. Never hallucinate."
    )


SYSTEM_PROMPT = _load_system_prompt()
PROMPT_VERSION = "v1"


def format_context(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks into context string with document tags.

    Uses <document> tags to prevent prompt injection from document content.
    Implements lost-in-the-middle mitigation: best chunk first AND last.
    """
    if not chunks:
        return ""

    # Lost-in-the-middle: put best chunk first AND last
    ordered = list(chunks)
    if len(ordered) > 2:
        best = ordered[0]
        middle = ordered[1:-1]
        last = ordered[-1]
        ordered = [best] + middle + [last, best]  # Duplicate best at end

    parts = []
    for i, chunk in enumerate(ordered, 1):
        parts.append(
            f'<document index="{i}" source="{chunk.document_name}" page="{chunk.page_number}">\n'
            f"{chunk.content}\n"
            f"</document>"
        )

    return "\n\n".join(parts)


def build_messages(
    question: str,
    context: str,
) -> list[dict[str, str]]:
    """Build the message list for the LLM call.

    Uses the versioned system prompt and formats the user message
    with context and question.
    """
    user_content = f"Document excerpts:\n\n{context}\n\nQuestion: {question}"

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


async def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
) -> AsyncGenerator[str, None]:
    """Full LCEL-style chain: format context → build messages → stream answer.

    Yields tokens as they arrive from the LLM.
    Logs which prompt version produced the answer.
    """
    from nexus.rag.llm_client import stream_tokens

    context = format_context(chunks)
    messages = build_messages(question, context)

    logger.info(
        "Generating answer",
        question=question[:80],
        context_chunks=len(chunks),
        prompt_version=PROMPT_VERSION,
    )

    async for token in stream_tokens(messages):
        yield token


async def generate_answer_full(
    question: str,
    chunks: list[RetrievedChunk],
) -> str:
    """Non-streaming version — returns the full answer string."""
    tokens: list[str] = []
    async for token in generate_answer(question, chunks):
        tokens.append(token)
    return "".join(tokens)
