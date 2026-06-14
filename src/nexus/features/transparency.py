"""Radical Transparency Mode — answer grounding & source verification.

Replaces the old similarity-derived "confidence score" (a single cosine number
dressed up as a percentage) with a *grounding* check: how much of the generated
answer is actually supported by the cited source excerpts. This is the visible
expression of RAGAS faithfulness — every claim is checked against the evidence
that was retrieved, which is far more defensible than an opaque confidence %.

Deterministic and free: reuses the in-stack all-MiniLM embeddings (no extra LLM
call). Returns structured data only; all human-readable labels live in the UI so
they localize cleanly (EN/FR).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

import numpy as np
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Callable

    from nexus.index.hybrid_retriever import RetrievedChunk


# Number of top source excerpts a claim can be grounded against. Matches the
# source cards shown in the UI, so every citation links to a visible source.
MATCH_K = 4
# Cosine threshold above which an answer claim counts as supported by a source.
GROUNDING_THRESHOLD = 0.45


class SourceRef(BaseModel):
    """A reference to a specific source document and excerpt."""

    document_name: str
    page_number: int
    excerpt: str
    section_header: str = ""


class GroundedClaim(BaseModel):
    """One statement from the answer and whether a source supports it."""

    text: str
    supported: bool
    source_index: int | None = None  # index into GroundingResult.sources
    similarity: float = 0.0


class GroundingResult(BaseModel):
    """Structured grounding output for a query response.

    Carries no prose — the UI renders localized labels from this structure so
    the feature reads natively in English and French.
    """

    verdict: Literal["grounded", "partial", "ungrounded"]
    coverage: float = Field(ge=0.0, le=1.0)  # supported claims / total claims
    supported_count: int = 0
    claim_count: int = 0
    claims: list[GroundedClaim] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    single_source: bool = False


def _split_claims(answer: str) -> list[str]:
    """Split an answer into verifiable statements.

    Strips markdown, splits on sentence/line boundaries, and drops fragments
    (headers, bullets, filler) shorter than five words so the coverage metric
    reflects real claims rather than connective tissue.
    """
    cleaned = re.sub(r"[#*`>_]+", " ", answer)
    raw = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
    claims: list[str] = []
    for sentence in raw:
        s = sentence.strip(" -•\t")
        if len(s.split()) >= 5:
            claims.append(s)
    return claims[:12]


def _cosine_to_rows(vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Cosine similarity of a single vector against each row of a matrix."""
    v = vec / (np.linalg.norm(vec) + 1e-9)
    m = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9)
    return m @ v


def build_grounding(
    answer: str,
    chunks: list[RetrievedChunk],
    embed_fn: Callable[[list[str]], list[list[float]]] | None = None,
) -> GroundingResult:
    """Verify how much of *answer* is supported by the retrieved *chunks*.

    Each answer claim is embedded and matched (cosine) against the top source
    excerpts. ``coverage`` is the fraction of claims with a supporting source
    above ``GROUNDING_THRESHOLD``; ``verdict`` bands that coverage. Because the
    answer is in the response language, the claims (and thus the UI) are too.

    ``embed_fn`` is injectable for testing; it defaults to the in-stack
    all-MiniLM embedder, imported lazily so the no-evidence paths never touch
    the embedding model.
    """
    match_chunks = chunks[:MATCH_K]
    sources = [
        SourceRef(
            document_name=c.document_name,
            page_number=c.page_number,
            excerpt=c.content[:200] + ("..." if len(c.content) > 200 else ""),
            section_header=c.section_header,
        )
        for c in match_chunks
    ]
    single_source = len({c.document_name for c in chunks}) <= 1

    if not match_chunks:
        return GroundingResult(
            verdict="ungrounded", coverage=0.0, sources=[], single_source=False
        )

    claim_texts = _split_claims(answer)
    if not claim_texts:
        # Nothing verifiable (empty or one-word answer) — cannot vouch for it.
        return GroundingResult(
            verdict="ungrounded",
            coverage=0.0,
            sources=sources,
            single_source=single_source,
        )

    if embed_fn is None:
        from nexus.rag.embeddings import embed_texts

        embed_fn = embed_texts

    vectors = embed_fn(claim_texts + [c.content for c in match_chunks])
    claim_vecs = np.asarray(vectors[: len(claim_texts)], dtype=float)
    chunk_vecs = np.asarray(vectors[len(claim_texts) :], dtype=float)

    claims: list[GroundedClaim] = []
    supported_count = 0
    for i, text in enumerate(claim_texts):
        sims = _cosine_to_rows(claim_vecs[i], chunk_vecs)
        best = int(np.argmax(sims))
        best_sim = float(sims[best])
        supported = best_sim >= GROUNDING_THRESHOLD
        if supported:
            supported_count += 1
        claims.append(
            GroundedClaim(
                text=text,
                supported=supported,
                source_index=best if supported else None,
                similarity=round(best_sim, 3),
            )
        )

    coverage = round(supported_count / len(claims), 2)
    if coverage >= 0.8:
        verdict: Literal["grounded", "partial", "ungrounded"] = "grounded"
    elif coverage >= 0.4:
        verdict = "partial"
    else:
        verdict = "ungrounded"

    return GroundingResult(
        verdict=verdict,
        coverage=coverage,
        supported_count=supported_count,
        claim_count=len(claims),
        claims=claims,
        sources=sources,
        single_source=single_source,
    )
