"""Tests for nexus.features.transparency — confidence scoring."""

from __future__ import annotations

import pytest

from nexus.features.transparency import TransparencyResult, build_transparency
from nexus.index.hybrid_retriever import RetrievedChunk


def _make_chunk(
    doc_name: str = "test.pdf",
    score: float = 0.5,
    content: str = "Test content",
    page: int = 1,
) -> RetrievedChunk:
    """Helper to create test chunks."""
    return RetrievedChunk(
        chunk_id=f"chunk-{doc_name}-{page}",
        document_name=doc_name,
        page_number=page,
        content=content,
        section_header="",
        score=score,
    )


class TestTransparency:
    """Test transparency / confidence scoring."""

    def test_no_chunks(self):
        """Empty chunks should produce low confidence."""
        result = build_transparency([])
        assert result.confidence == "low"
        assert result.confidence_score == 0.0
        assert len(result.sources) == 0

    def test_high_confidence(self):
        """High-scoring chunks from multiple docs should give high confidence."""
        chunks = [
            _make_chunk("doc1.pdf", score=0.8),
            _make_chunk("doc2.pdf", score=0.75),
            _make_chunk("doc3.pdf", score=0.7),
        ]
        result = build_transparency(chunks)
        assert result.confidence == "high"
        assert result.confidence_score >= 0.75

    def test_multi_source_boost(self):
        """Multiple unique documents should boost confidence."""
        single_doc = [_make_chunk("same.pdf", score=0.6, page=i) for i in range(3)]
        multi_doc = [_make_chunk(f"doc{i}.pdf", score=0.6) for i in range(3)]

        single_result = build_transparency(single_doc)
        multi_result = build_transparency(multi_doc)

        assert multi_result.confidence_score >= single_result.confidence_score

    def test_low_confidence_caveats(self):
        """Low confidence should include caveats."""
        chunks = [_make_chunk(score=0.1)]
        result = build_transparency(chunks)
        assert len(result.caveats) > 0

    def test_sources_limited_to_4(self):
        """Should not return more than 4 sources."""
        chunks = [_make_chunk(f"doc{i}.pdf", score=0.5) for i in range(10)]
        result = build_transparency(chunks)
        assert len(result.sources) <= 4

    def test_result_is_valid_model(self):
        """Result should be a valid Pydantic model."""
        chunks = [_make_chunk(score=0.5)]
        result = build_transparency(chunks)
        assert isinstance(result, TransparencyResult)
        # Should serialize without error
        data = result.model_dump()
        assert "confidence" in data
        assert "sources" in data
