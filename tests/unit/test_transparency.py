"""Tests for nexus.features.transparency — answer grounding / source verification.

The embedder is injected (embed_fn) so these tests stay pure and fast — no
sentence-transformers model is loaded.
"""

from __future__ import annotations

import pytest

from nexus.features.transparency import (
    GROUNDING_THRESHOLD,
    GroundedClaim,
    GroundingResult,
    SourceRef,
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
    """Deterministic embed_fn stub.

    build_grounding calls embed_fn(claims + chunk_contents) in that order.
    """
    return lambda _texts: claim_vecs + chunk_vecs


# Two sentences, each ≥ 5 words
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

    def test_empty_string_returns_empty(self):
        assert _split_claims("") == []

    def test_single_word_returns_empty(self):
        assert _split_claims("OK") == []

    def test_markdown_stripped_before_split(self):
        """Markdown formatting characters should not appear in claim text."""
        claims = _split_claims("**Bold** claim about the remote work policy here.")
        assert all("<" not in c and "**" not in c for c in claims)

    def test_max_claims_capped(self):
        """Should not return more than 12 claims (internal cap)."""
        many_sentences = " ".join(
            f"This is sentence number {i} about company policy." for i in range(20)
        )
        claims = _split_claims(many_sentences)
        assert len(claims) <= 12

    def test_bullet_points_ignored(self):
        """Bullet-point fragments shorter than 5 words should be filtered."""
        text = "- Item A\n- Item B\nThis is a proper full sentence about policy here."
        claims = _split_claims(text)
        assert any("proper full sentence" in c for c in claims)


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
        """Chunks from one document → single_source=True."""
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            [_make_chunk("same.pdf", page=1)],
            embed_fn=_embedder([[1.0, 0.0], [1.0, 0.0]], [[1.0, 0.0]]),
        )
        assert result.single_source is True

    def test_multi_source_flag(self):
        """Chunks from 2+ documents → single_source=False."""
        chunks = [_make_chunk("a.pdf"), _make_chunk("b.pdf")]
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            chunks,
            embed_fn=_embedder([[1.0, 0.0], [1.0, 0.0]], [[1.0, 0.0], [1.0, 0.0]]),
        )
        assert result.single_source is False

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

    def test_coverage_in_range(self):
        """coverage must always be in [0.0, 1.0]."""
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            [_make_chunk()],
            embed_fn=_embedder([[1.0, 0.0], [1.0, 0.0]], [[1.0, 0.0]]),
        )
        assert 0.0 <= result.coverage <= 1.0

    def test_verdict_values(self):
        """Verdict must be one of three valid strings."""
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            [_make_chunk()],
            embed_fn=_embedder([[1.0, 0.0], [1.0, 0.0]], [[1.0, 0.0]]),
        )
        assert result.verdict in ("grounded", "partial", "ungrounded")

    def test_no_verifiable_claims_ungrounded(self):
        """An answer with no sentences ≥ 5 words produces ungrounded result."""
        result = build_grounding("Yes.", [_make_chunk()])
        assert result.verdict == "ungrounded"
        assert result.coverage == 0.0

    def test_excerpt_truncated_to_200_chars(self):
        """Source excerpts in SourceRef must be ≤ 203 chars (200 + '...')."""
        long_content = "A" * 500
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            [_make_chunk(content=long_content)],
            embed_fn=_embedder([[1.0, 0.0], [1.0, 0.0]], [[1.0, 0.0]]),
        )
        for src in result.sources:
            assert len(src.excerpt) <= 203  # 200 chars + "..."

    def test_claim_count_matches_claims_list(self):
        """claim_count must equal len(claims)."""
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            [_make_chunk()],
            embed_fn=_embedder([[1.0, 0.0], [1.0, 0.0]], [[1.0, 0.0]]),
        )
        assert result.claim_count == len(result.claims)

    def test_grounding_threshold_constant_in_range(self):
        """GROUNDING_THRESHOLD must be between 0 and 1 (sanity check on module constant)."""
        assert 0.0 < GROUNDING_THRESHOLD < 1.0

    def test_source_ref_fields_populated(self):
        """Each SourceRef must have non-empty document_name and page_number >= 1."""
        result = build_grounding(
            TWO_CLAIM_ANSWER,
            [_make_chunk("hr_policy.pdf", page=3)],
            embed_fn=_embedder([[1.0, 0.0], [1.0, 0.0]], [[1.0, 0.0]]),
        )
        for src in result.sources:
            assert src.document_name
            assert src.page_number >= 1
