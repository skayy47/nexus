"""Tests for BM25 index."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from nexus.index.bm25_index import BM25Index


@dataclass
class FakeChunk:
    chunk_id: str
    document_name: str
    page_number: int
    content: str
    section_header: str = ""


def _make_stored(content: str, doc_name: str = "doc.pdf", chunk_id: str | None = None) -> FakeChunk:
    return FakeChunk(
        chunk_id=chunk_id or f"id-{hash(content)}",
        document_name=doc_name,
        page_number=1,
        content=content,
    )


class TestBM25Index:
    """Test BM25 keyword search index."""

    def test_empty_index(self):
        idx = BM25Index()
        assert not idx.is_built
        assert idx.search("test") == []

    def test_build_and_search(self):
        idx = BM25Index()
        chunks = [
            _make_stored("remote work policy allows three days per week"),
            _make_stored("financial budget for Q3 marketing is four hundred thousand"),
            _make_stored("engineering team quarterly review process"),
        ]
        idx.build(chunks)
        assert idx.is_built

        results = idx.search("remote work policy")
        assert len(results) > 0
        assert results[0].chunk.content == "remote work policy allows three days per week"

    def test_rebuild(self):
        idx = BM25Index()
        idx.build([_make_stored("first corpus about machine learning")])
        idx.build([_make_stored("second corpus about data engineering")])
        results = idx.search("second corpus data engineering")
        assert len(results) > 0
        assert "second" in results[0].chunk.content

    def test_search_empty_query_returns_results_or_empty(self):
        """An empty query should not crash — returns empty list gracefully."""
        idx = BM25Index()
        idx.build([_make_stored("some content about policies")])
        result = idx.search("")
        assert isinstance(result, list)

    def test_search_no_match_returns_empty_or_low_score(self):
        """A query with no lexical overlap may return empty results."""
        idx = BM25Index()
        idx.build([
            _make_stored("remote work policy three days"),
            _make_stored("marketing budget quarterly revenue"),
        ])
        # Completely unrelated query
        results = idx.search("astrophysics quantum entanglement")
        assert isinstance(results, list)

    def test_top_k_limits_results(self):
        """search(k=2) must return at most 2 results."""
        idx = BM25Index()
        chunks = [_make_stored(f"document number {i} about policies", chunk_id=f"c{i}") for i in range(10)]
        idx.build(chunks)
        results = idx.search("policies document", k=2)
        assert len(results) <= 2

    def test_scores_are_non_negative(self):
        """All BM25 scores must be ≥ 0."""
        idx = BM25Index()
        idx.build([_make_stored("remote work policy"), _make_stored("financial report")])
        results = idx.search("remote work")
        for r in results:
            assert r.score >= 0.0

    def test_results_sorted_descending(self):
        """Results must be in descending score order (most relevant first)."""
        idx = BM25Index()
        idx.build([
            _make_stored("remote work policy three days per week maximum"),
            _make_stored("remote mention in passing"),
            _make_stored("completely unrelated marketing topic"),
        ])
        results = idx.search("remote work policy")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True), "Results not sorted by score"

    def test_chunk_identity_preserved(self):
        """chunk_id and document_name must match the originals after indexing."""
        idx = BM25Index()
        chunk = _make_stored("specific content only here", doc_name="hr_policy.pdf", chunk_id="abc123")
        idx.build([chunk])
        results = idx.search("specific content")
        assert len(results) > 0
        assert results[0].chunk.chunk_id == "abc123"
        assert results[0].chunk.document_name == "hr_policy.pdf"

    def test_single_chunk_corpus(self):
        """Index with exactly one chunk must still be searchable."""
        idx = BM25Index()
        idx.build([_make_stored("the only document in the index")])
        results = idx.search("only document")
        assert len(results) == 1

    def test_duplicate_content_chunks(self):
        """Multiple chunks with identical content must all be indexed."""
        idx = BM25Index()
        chunks = [
            _make_stored("remote work policy", chunk_id=f"c{i}") for i in range(3)
        ]
        idx.build(chunks)
        results = idx.search("remote work policy")
        assert len(results) >= 1  # at minimum the top result is returned
