"""Confidence scoring and source attribution from retrieval results."""
from pydantic import BaseModel

from core.retrieval import RetrievedChunk


class SourceRef(BaseModel):
    document_name: str
    page_number: int
    excerpt: str


class ConfidenceResult(BaseModel):
    score: float          # 0.0 – 1.0
    label: str            # "high" | "moderate" | "low"
    reasoning: str
    sources: list[SourceRef]


def build_confidence(chunks: list[RetrievedChunk]) -> ConfidenceResult:
    if not chunks:
        return ConfidenceResult(
            score=0.0, label="low",
            reasoning="No relevant documents found.",
            sources=[]
        )

    # Normalize RRF scores to 0-1 range
    max_score = max(c.score for c in chunks)
    if max_score == 0:
        avg_norm = 0.0
    else:
        avg_norm = sum(c.score / max_score for c in chunks[:3]) / min(3, len(chunks))

    # Boost confidence when multiple unique documents agree
    unique_docs = len({c.document_name for c in chunks})
    multi_source_boost = 0.1 if unique_docs >= 2 else 0.0

    score = min(1.0, round(avg_norm + multi_source_boost, 2))

    if score >= 0.75:
        label, reasoning = "high", f"Answer is supported by {unique_docs} document(s) with strong relevance."
    elif score >= 0.5:
        label, reasoning = "moderate", f"Answer is partially supported — {unique_docs} document(s) found but with moderate relevance."
    else:
        label, reasoning = "low", "Relevant documents found but with weak match to the query."

    sources = [
        SourceRef(
            document_name=c.document_name,
            page_number=c.page_number,
            excerpt=c.content[:200] + ("..." if len(c.content) > 200 else ""),
        )
        for c in chunks[:4]
    ]

    return ConfidenceResult(score=score, label=label, reasoning=reasoning, sources=sources)
