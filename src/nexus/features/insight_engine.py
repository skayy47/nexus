"""Cross-Document Insight Engine — surfaces non-obvious connections.

Phase 2 stub.
"""

from __future__ import annotations

from pydantic import BaseModel


class Insight(BaseModel):
    """A non-obvious connection across multiple documents."""

    description: str
    source_documents: list[str]  # Must cite ≥2 sources or rejected
    actionable: bool = True
    confidence: float = 0.0


async def generate_insights() -> list[Insight]:
    """Generate cross-document insights via chunk clustering + LLM.

    Stub — full implementation in Phase 2.
    """
    return []
