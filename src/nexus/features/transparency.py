"""Radical Transparency Mode — confidence scoring and plain-English reasoning.

Phase 2 implementation. This stub provides the data models and
a basic confidence scorer based on retrieval scores.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from nexus.index.hybrid_retriever import RetrievedChunk


class SourceRef(BaseModel):
    """A reference to a specific source document and excerpt."""

    document_name: str
    page_number: int
    excerpt: str
    section_header: str = ""


class TransparencyResult(BaseModel):
    """Full transparency output for a query response."""

    confidence: Literal["low", "medium", "high"]
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    sources: list[SourceRef]
    caveats: list[str] = Field(default_factory=list)


def build_transparency(chunks: list[RetrievedChunk]) -> TransparencyResult:
    """Build transparency metadata from retrieved chunks.

    Confidence is a function of:
    - Retrieval score distribution
    - Chunk agreement (same topic from multiple docs)
    - Score magnitude
    """
    if not chunks:
        return TransparencyResult(
            confidence="low",
            confidence_score=0.0,
            reasoning="No relevant documents found in the knowledge base.",
            sources=[],
            caveats=["No documents matched this query."],
        )

    # Normalize RRF scores to 0-1
    max_score = max(c.score for c in chunks)
    if max_score == 0:
        avg_norm = 0.0
    else:
        top_3 = chunks[:3]
        avg_norm = sum(c.score / max_score for c in top_3) / len(top_3)

    # Multi-source agreement boost
    unique_docs = len({c.document_name for c in chunks})
    multi_source_boost = 0.1 if unique_docs >= 2 else 0.0

    score = min(1.0, round(avg_norm + multi_source_boost, 2))

    # Determine confidence level and reasoning
    if score >= 0.75:
        confidence: Literal["low", "medium", "high"] = "high"
        reasoning = (
            f"I found {len(chunks)} relevant excerpts across {unique_docs} document(s), "
            f"all with strong relevance to your question."
        )
    elif score >= 0.50:
        confidence = "medium"
        reasoning = (
            f"I found {len(chunks)} excerpts across {unique_docs} document(s), "
            f"but the match quality is moderate. The answer may be incomplete."
        )
    else:
        confidence = "low"
        reasoning = (
            f"I found {len(chunks)} excerpts but with weak relevance scores. "
            f"The knowledge base may not contain a direct answer to this question."
        )

    # Build source references
    sources = [
        SourceRef(
            document_name=c.document_name,
            page_number=c.page_number,
            excerpt=c.content[:200] + ("..." if len(c.content) > 200 else ""),
            section_header=c.section_header,
        )
        for c in chunks[:4]
    ]

    # Caveats
    caveats: list[str] = []
    if unique_docs == 1:
        caveats.append("Answer based on a single document source.")
    if score < 0.5:
        caveats.append("Low retrieval confidence — consider uploading more relevant documents.")

    return TransparencyResult(
        confidence=confidence,
        confidence_score=score,
        reasoning=reasoning,
        sources=sources,
        caveats=caveats,
    )
