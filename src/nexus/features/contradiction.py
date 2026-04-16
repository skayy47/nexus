"""Contradiction Radar — detects conflicting statements across documents.

Uses a second LLM call with structured output to compare retrieved chunks.
Triggered after every RAG response when >= 2 documents are in context.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel

if TYPE_CHECKING:
    from nexus.index.hybrid_retriever import RetrievedChunk

logger = structlog.get_logger(__name__)


class ContradictionResult(BaseModel):
    """Detected contradiction between two document excerpts."""

    excerpt_a: str
    excerpt_b: str
    source_a: str
    source_b: str
    page_a: int = 1
    page_b: int = 1
    explanation: str
    severity: str = "high"  # "high" | "medium" | "low"


_CONTRADICTION_PROMPT = """\
You are a contradiction detector for a document intelligence system.

Below are excerpts from company documents. Your job is to identify if any two excerpts \
contain FACTUAL CONTRADICTIONS — statements that cannot both be true at the same time.

Focus on:
- Different numbers for the same metric (budgets, limits, counts)
- Conflicting rules or policies on the same topic
- Opposing claims about a project, person, or event status

DO NOT flag:
- Different perspectives or opinions
- Information from different time periods where one clearly supersedes another
- Complementary information that adds detail

Documents:
{documents}

Respond in JSON with this exact structure:
{{
  "contradiction_found": true or false,
  "excerpt_a": "the first conflicting statement (exact quote, max 200 chars)",
  "excerpt_b": "the second conflicting statement (exact quote, max 200 chars)",
  "source_a": "document name for excerpt_a",
  "source_b": "document name for excerpt_b",
  "explanation": "one sentence explaining the contradiction",
  "severity": "high" or "medium" or "low"
}}

If no contradiction found, return: {{"contradiction_found": false}}
"""


def _format_chunks_for_contradiction(chunks: list[RetrievedChunk]) -> str:
    """Format chunks from different documents for the contradiction check.

    Takes up to 3 chunks per document, each shown in full (up to 500 chars),
    so the LLM sees enough content to surface contradictions even when the
    key sentence appears later in a chunk.
    """
    # Group chunks by document — up to 3 per doc, max 4 docs
    doc_chunks: dict[str, list[RetrievedChunk]] = {}
    for chunk in chunks:
        if chunk.document_name not in doc_chunks:
            doc_chunks[chunk.document_name] = []
        if len(doc_chunks[chunk.document_name]) < 3:
            doc_chunks[chunk.document_name].append(chunk)

    parts = []
    for doc_name, doc_chunk_list in list(doc_chunks.items())[:4]:
        # Show each chunk separately so truncation doesn't bury key sentences
        chunk_texts = [f"  ...{c.content[:500]}..." for c in doc_chunk_list]
        combined = "\n".join(chunk_texts)
        parts.append(f"[{doc_name}]\n{combined}")
    return "\n\n---\n\n".join(parts)


async def detect_contradictions(
    chunks: list[RetrievedChunk],
) -> ContradictionResult | None:
    """Detect contradictions among retrieved chunks via second LLM call.

    Only runs when chunks come from >= 2 different documents.
    Returns None if no contradiction detected or only one source present.
    """
    # Only check for contradictions when we have multiple source documents
    unique_docs = {c.document_name for c in chunks}
    if len(unique_docs) < 2:
        return None

    from nexus.rag.llm_client import single_call

    doc_text = _format_chunks_for_contradiction(chunks)
    prompt = _CONTRADICTION_PROMPT.format(documents=doc_text)

    try:
        raw = await single_call(prompt, max_tokens=400, temperature=0.0)

        # Extract JSON from response (LLMs sometimes wrap it in markdown)
        raw = raw.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)

        if not data.get("contradiction_found"):
            return None

        return ContradictionResult(
            excerpt_a=data.get("excerpt_a", "")[:300],
            excerpt_b=data.get("excerpt_b", "")[:300],
            source_a=data.get("source_a", "Unknown"),
            source_b=data.get("source_b", "Unknown"),
            explanation=data.get("explanation", ""),
            severity=data.get("severity", "high"),
        )

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Contradiction parse failed", error=str(e), raw=raw[:200])
        return None
    except Exception as e:
        logger.error("Contradiction detection failed", error=str(e))
        return None
