"""Groq client — streaming answer generation."""
from typing import AsyncGenerator

from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import get_settings
from core.retrieval import RetrievedChunk

settings = get_settings()

_client = AsyncGroq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """You are NEXUS, an institutional memory engine.
Answer questions strictly based on the provided document excerpts.
Always cite which document(s) support your answer.
If the documents contradict each other, note it explicitly.
If the documents don't contain the answer, say so — never hallucinate."""


def _build_context(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"[{i}] Source: {chunk.document_name} (page {chunk.page_number})\n{chunk.content}"
        )
    return "\n\n---\n\n".join(parts)


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def stream_answer(
    question: str, chunks: list[RetrievedChunk]
) -> AsyncGenerator[str, None]:
    context = _build_context(chunks)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Document excerpts:\n\n{context}\n\nQuestion: {question}",
        },
    ]

    stream = await _client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        stream=True,
        temperature=0.1,
        max_tokens=1024,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


async def single_call(prompt: str, max_tokens: int = 512) -> str:
    """Non-streaming single call for contradiction detection."""
    response = await _client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        temperature=0.0,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""
