"""Tests for nexus.features.transparency — answer grounding / source verification.

The embedder is injected (embed_fn) so these tests stay pure and fast — no
sentence-transformers model is loaded.
"""

from __future__ import annotations

from nexus.features.transparency import (
    GroundingResult,
    _split_claims,
    build_grounding,
)
from nexus.index.hybrid_retriever import RetrievedChunk


def _make_chunk(
    doc_name: str = "test.pdf",
    score: float = 0.5,
    content: str = "Test content about the remote work policy and weekly limits.",
    page: int = 1,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"chunk-{doc_name}-{page}",
        document_name=doc_name,
        page_number=page,
        content=content,
        section_header="",
        score=score,
    )


def _embedder(claim_vecs, chunk_vecs):
    """A deterministic embed_fn stub.

    build_grounding calls embed_fn(claims + chunk_contents) in that order, so the
    stub returns the supplied claim vectors followed by the chunk vectors.
    """
    return lambda _texts: claim_vecs + chunk_vecs


# Two sentences, each ≥ 5 words → _split_claims yields exactly two claims.
TWO_CLAIM_ANSWER = (
    "The remote work policy allows three days each week. "
    "Employees may also work fully from home."
)


class TestSplitClaims:
    def test_filters_short_fragments(self):
        claims = _split_claims("# Heading\nok\nThis sentence has more than five words here.")
        assert claims == ["This sentence has more than five words here."]

    def test_two_sentences(self):
        assert len(_split_claims(TWO_CLAIM_ANSWER)) == 2


class TestGrounding:
    def test_no_chunks(self):
        """No retrieved chunks → ungrounded, zero coverage, no sources."""
        result = build_grounding("Any answer text at all here.", [])
        assert result.verdict == "ungrounded"
        assert result.coverage == 0.0
        assert result.sources == []

    def test_fully_grounded(self):
        """Every claim aligned with a source → grounded, coverage 1.0."""
        chunks = [_make_chunk("doc1.pdf"), _make_chunk("doc2.pdf")]
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            chunks,
            embed_fn=_embedder([[1.0, 0.0], [1.0, 0.0]], [[1.0, 0.0], [1.0, 0.0]]),
        )
        assert result.verdict == "grounded"
        assert result.coverage == 1.0
        assert result.supported_count == 2
        assert all(c.supported and c.source_index is not None for c in result.claims)

    def test_ungrounded(self):
        """Claims orthogonal to every source → ungrounded, coverage 0.0."""
        chunks = [_make_chunk("doc1.pdf"), _make_chunk("doc2.pdf")]
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            chunks,
            embed_fn=_embedder([[0.0, 1.0], [0.0, 1.0]], [[1.0, 0.0], [1.0, 0.0]]),
        )
        assert result.verdict == "ungrounded"
        assert result.coverage == 0.0
        assert all(not c.supported and c.source_index is None for c in result.claims)

    def test_partial(self):
        """One of two claims supported → partial, coverage 0.5."""
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            [_make_chunk("doc1.pdf")],
            embed_fn=_embedder([[1.0, 0.0], [0.0, 1.0]], [[1.0, 0.0]]),
        )
        assert result.verdict == "partial"
        assert result.coverage == 0.5
        assert result.supported_count == 1

    def test_single_source_flag(self):
        """Chunks from one document set single_source=True."""
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            [_make_chunk("same.pdf", page=1)],
            embed_fn=_embedder([[1.0, 0.0], [1.0, 0.0]], [[1.0, 0.0]]),
        )
        assert result.single_source is True

    def test_sources_limited_to_4(self):
        """Never expose more than MATCH_K (4) source cards."""
        chunks = [_make_chunk(f"doc{i}.pdf") for i in range(10)]
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            chunks,
            embed_fn=_embedder([[1.0, 0.0], [1.0, 0.0]], [[1.0, 0.0]] * 4),
        )
        assert len(result.sources) <= 4

    def test_valid_model_dump(self):
        """Result serializes with the grounding schema."""
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            [_make_chunk()],
            embed_fn=_embedder([[1.0, 0.0], [1.0, 0.0]], [[1.0, 0.0]]),
        )
        assert isinstance(result, GroundingResult)
        data = result.model_dump()
        assert "verdict" in data
        assert "coverage" in data
        assert "claims" in data
        assert "sources" in data
