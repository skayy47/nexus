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


# Match all retrieved chunks (up to retrieval_k=8) so no source chunk is missed.
MATCH_K = 8
# Cosine threshold above which an answer claim counts as supported by a source.
GROUNDING_THRESHOLD = 0.40
# In-text citation pattern: [filename, page N, ...] or [filename, page="N"]
_CITATION_RE = re.compile(r"\[([^\]]+?)[,\s]+page[^\]]*\]", re.IGNORECASE)


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


def _normalize_name(name: str) -> str:
    """Normalize a filename for fuzzy comparison: strip punctuation, lowercase.

    "Hands+on+Lab.pdf", "Hands on Lab.pdf", and "Hands_on_Lab.pdf" all become
    "handsonlabpdf", so LLM-reformatted filenames (spaces/underscores/+ signs)
    still match the stored name.
    """
    return re.sub(r"[\s_+./()\-]+", "", name).lower()


def _extract_cited_doc(text: str) -> str | None:
    """Return the document name from an inline citation, or None if not present.

    Matches patterns like:
      [TechCorp_HR_Policy_2024.txt, page 1, document index 4]
      [chahbi_zouhair_cv_final.pdf, page="1" (document index 3)]
    """
    m = _CITATION_RE.search(text)
    if m:
        return m.group(1).strip()
    return None


def _strip_citations(text: str) -> str:
    """Remove inline citation brackets so the claim text embeds cleanly."""
    return _CITATION_RE.sub("", text).strip()


def _split_claims(answer: str) -> list[str]:
    """Split an answer into verifiable statements.

    Strips markdown + inline citations, splits on sentence/line boundaries,
    and drops very short fragments (< 3 words) that are connective tissue.
    Returns at most 12 claims.
    """
    # Remove markdown emphasis markers
    cleaned = re.sub(r"[#*`>_]+", " ", answer)
    # Remove citation brackets before splitting so they don't distort claim length
    cleaned = _CITATION_RE.sub("", cleaned)
    raw = re.split(r"(?<=[.!?])\s+|\n+", cleaned)
    claims: list[str] = []
    for sentence in raw:
        s = sentence.strip(" -•\t")
        if len(s.split()) >= 3:
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

    Two grounding paths:
    1. **Citation-aware**: if a claim contains an inline citation referencing one
       of the retrieved documents, it is grounded by citation — no embedding
       needed. This correctly handles list-style answers where the LLM embeds
       source references inline (e.g. skills extracted from a CV).
    2. **Semantic similarity**: for claims without inline citations, embed the
       claim (citation-stripped) and compare cosine against chunk embeddings.
       Threshold is GROUNDING_THRESHOLD (0.40).

    ``coverage`` is the fraction of claims with a supporting source;
    ``verdict`` bands that coverage (≥0.8 → grounded, ≥0.4 → partial).
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
    retrieved_doc_names = {c.document_name for c in match_chunks}

    if not match_chunks:
        return GroundingResult(verdict="ungrounded", coverage=0.0, sources=[], single_source=False)

    # Split the raw answer into claims (citations already stripped inside)
    # We need both the raw claim lines (to detect inline citations) and
    # the stripped versions (for semantic embedding).
    raw_answer_lines = re.sub(r"[#*`>_]+", " ", answer)
    raw_lines = [
        s.strip(" -•\t")
        for s in re.split(r"(?<=[.!?])\s+|\n+", raw_answer_lines)
        if len(s.strip(" -•\t").split()) >= 3
    ][:12]

    if not raw_lines:
        return GroundingResult(
            verdict="ungrounded",
            coverage=0.0,
            sources=sources,
            single_source=single_source,
        )

    if embed_fn is None:
        from nexus.rag.embeddings import embed_texts

        embed_fn = embed_texts

    # Strip citations for embedding (keeps semantic signal clean)
    stripped_lines = [_strip_citations(line) for line in raw_lines]

    # Embed stripped claims + all chunk contents together
    chunk_texts = [c.content for c in match_chunks]
    all_texts = stripped_lines + chunk_texts
    vectors = embed_fn(all_texts)
    claim_vecs = np.asarray(vectors[: len(stripped_lines)], dtype=float)
    chunk_vecs = np.asarray(vectors[len(stripped_lines) :], dtype=float)

    claims: list[GroundedClaim] = []
    supported_count = 0

    for i, raw_line in enumerate(raw_lines):
        display_text = _strip_citations(raw_line).strip() or raw_line.strip()

        # Path 1: citation-aware grounding (fuzzy name match handles LLM-reformatted filenames,
        # e.g. "chahbi zouhair cv final.pdf" matching "chahbi_zouhair_cv_final.pdf")
        cited_doc = _extract_cited_doc(raw_line)
        cited_doc_norm = _normalize_name(cited_doc) if cited_doc else None
        if cited_doc_norm and any(
            _normalize_name(n) == cited_doc_norm for n in retrieved_doc_names
        ):
            # LLM cited a document that was actually retrieved → grounded
            supported = True
            best = next(
                (
                    j
                    for j, c in enumerate(match_chunks)
                    if _normalize_name(c.document_name) == cited_doc_norm
                ),
                0,
            )
            best_sim = 1.0
        else:
            # Path 2: semantic similarity on citation-stripped claim
            sims = _cosine_to_rows(claim_vecs[i], chunk_vecs)
            best = int(np.argmax(sims))
            best_sim = float(sims[best])
            supported = best_sim >= GROUNDING_THRESHOLD

        if supported:
            supported_count += 1
        claims.append(
            GroundedClaim(
                text=display_text,
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
