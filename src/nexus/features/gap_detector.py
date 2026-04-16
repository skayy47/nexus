"""Knowledge Gap Detective — flags missing information in the corpus.

Phase 2 stub.
"""

from __future__ import annotations

from pydantic import BaseModel


class GapReport(BaseModel):
    """A detected knowledge gap in the corpus."""

    topic: str
    description: str
    last_related_doc: str = ""
    last_related_date: str = ""
    severity: str = "medium"


async def detect_gaps(query: str, confidence_score: float) -> list[GapReport]:
    """Detect knowledge gaps triggered by a query.

    Stub — full implementation in Phase 2.
    """
    return []


async def scan_corpus_gaps() -> list[GapReport]:
    """On-demand corpus scan for missing topics.

    Stub — full implementation in Phase 2.
    """
    return []
