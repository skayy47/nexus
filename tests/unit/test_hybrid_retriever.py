"""Tests for hybrid_retrieve — regression coverage for the cross-document
contradiction retrieval bug (marketing-budget question missing the Q4 chunk
because dense similarity diluted a table-heavy chunk's one relevant line).

Before this file, hybrid_retrieve had zero test coverage — only the BM25-only
layer (test_bm25.py) was exercised.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

import pytest

from nexus.index.bm25_index import get_bm25_index
from nexus.index.hybrid_retriever import DENSE_WEIGHT, SPARSE_WEIGHT, hybrid_retrieve


@dataclass
class FakeStoredChunk:
    chunk_id: str
    document_name: str
    page_number: int
    content: str
    section_header: str = ""
    score: float = 0.0


# The exact real-world chunk that was missing from retrieval: a full-year
# OPEX table where the one relevant line ("Q3 Marketing: $380,000") is
# diluted by four unrelated line items sharing the chunk.
Q4_TARGET_CONTENT = (
    "Full-year 2023 operating expense summary: Personnel costs totaled "
    "$27.8 million. Infrastructure spending reached $4.2 million. Research "
    "and development totaled $6.1 million. General and administrative "
    "expenses were $3.9 million. Of which, Q3 Marketing: $380,000."
)

Q3_DOC_CONTENT = (
    "The Q3 2023 marketing budget was fully deployed at $450,000 across "
    "digital and print campaigns this quarter."
)

DISTRACTOR_CONTENTS = [
    "Eligible employees may work remotely for up to three days per week under the 2023 policy.",
    "Eligible employees may work remotely for up to two days per week under the 2024 policy.",
    "Remote workdays must be pre-approved by the employee's direct manager in advance.",
    "Employees approved for remote work receive a one-time equipment allowance.",
    "Project Atlas was marked complete in Q4 2023 and moved to maintenance phase.",
    "The engineering team conducts quarterly roadmap review sessions.",
    "Parental leave was extended to sixteen weeks under the 2024 HR policy.",
    "General office hours are nine to five, Monday through Friday.",
    "The customer support team handles escalations within one business day.",
    "Annual performance reviews are conducted every December.",
]


def _make_chunk(chunk_id: str, content: str, doc_name: str = "doc.pdf") -> FakeStoredChunk:
    return FakeStoredChunk(chunk_id=chunk_id, document_name=doc_name, page_number=1, content=content)


@pytest.fixture(autouse=True)
def _real_bm25_index():
    """Build the real BM25 singleton with a corpus that includes the target
    chunk, so BM25 scoring is genuinely exercised (this is what actually
    caught the original bug — not a mock).
    """
    idx = get_bm25_index()
    chunks = [
        _make_chunk("q3-budget", Q3_DOC_CONTENT, "Q3_2023_Financial_Summary.txt"),
        _make_chunk("q4-opex-target", Q4_TARGET_CONTENT, "Q4_2023_Financial_Summary.txt"),
    ] + [_make_chunk(f"distractor-{i}", c) for i, c in enumerate(DISTRACTOR_CONTENTS)]
    idx.build(chunks)
    yield
    idx.build([])  # reset the singleton so other tests aren't affected


class TestHybridRetrieveContradictionRegression:
    """Regression test for the Q3/Q4 marketing-budget retrieval gap."""

    @pytest.mark.asyncio
    async def test_diluted_dense_chunk_still_retrieved_via_bm25(self):
        """Even when the target chunk ranks low on dense similarity (simulating
        the observed dilution from an OPEX table), it must still surface in
        the fused top-k because BM25 ranks it highly on lexical overlap.
        """
        query = "What was TechCorp's marketing budget spent in Q3 2023?"

        # Simulate the diagnosed dilution: dense similarity ranks the target
        # chunk near the bottom (position 9 of 12) because its embedding is
        # dominated by unrelated OPEX line items, not the one relevant figure.
        dense_order = (
            ["q3-budget"]
            + [f"distractor-{i}" for i in range(8)]
            + ["q4-opex-target"]
            + [f"distractor-{i}" for i in range(8, 10)]
        )
        dense_results = [
            FakeStoredChunk(
                chunk_id=cid,
                document_name="doc.pdf",
                page_number=1,
                content=Q3_DOC_CONTENT if cid == "q3-budget" else Q4_TARGET_CONTENT if cid == "q4-opex-target" else "distractor",
                score=1.0 - (rank * 0.05),
            )
            for rank, cid in enumerate(dense_order)
        ]

        with patch("nexus.index.supabase_store.similarity_search", new=AsyncMock(return_value=dense_results)):
            results = await hybrid_retrieve(query, query_embedding=[0.0] * 384, k=10)

        result_ids = {r.chunk_id for r in results}
        assert "q4-opex-target" in result_ids, (
            "The Q4 budget contradiction chunk was not retrieved — this is the "
            "exact regression this test guards against."
        )
        assert "q3-budget" in result_ids, "The Q3 chunk should also be retrieved (it's the strongest match on both signals)."

    def test_sparse_weight_at_least_dense_weight(self):
        """Locks in the intent of the RRF weighting fix — a future refactor
        that silently resets weights to equal (or inverts them) should fail
        this test immediately.
        """
        assert SPARSE_WEIGHT >= DENSE_WEIGHT
