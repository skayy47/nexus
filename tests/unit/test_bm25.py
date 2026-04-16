"""Tests for BM25 index."""

from __future__ import annotations

from dataclasses import dataclass

from nexus.index.bm25_index import BM25Index


@dataclass
class FakeChunk:
    chunk_id: str
    document_name: str
    page_number: int
    content: str
    section_header: str = ""


def _make_stored(content: str, doc_name: str = "doc.pdf") -> FakeChunk:
    return FakeChunk(
        chunk_id=f"id-{hash(content)}",
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
