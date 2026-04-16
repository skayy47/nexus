"""Tests for the RAG chain — context formatting, prompt loading."""

from __future__ import annotations

from nexus.index.hybrid_retriever import RetrievedChunk
from nexus.rag.chain import PROMPT_VERSION, SYSTEM_PROMPT, build_messages, format_context


def _make_chunk(doc: str = "test.pdf", page: int = 1, content: str = "chunk") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="cid",
        document_name=doc,
        page_number=page,
        content=content,
        section_header="",
        score=0.5,
    )


class TestChain:
    def test_prompt_loaded(self):
        """System prompt should be loaded from the versioned .md file."""
        assert "NEXUS" in SYSTEM_PROMPT
        assert PROMPT_VERSION == "v1"

    def test_format_context_empty(self):
        assert format_context([]) == ""

    def test_format_context_document_tags(self):
        """Context should use <document> tags for injection protection."""
        chunks = [_make_chunk(content="some text")]
        ctx = format_context(chunks)
        assert "<document" in ctx
        assert "some text" in ctx
        assert "</document>" in ctx

    def test_format_context_lost_in_middle(self):
        """With >2 chunks, best chunk should appear first AND last."""
        chunks = [
            _make_chunk(content="BEST"),
            _make_chunk(content="middle1"),
            _make_chunk(content="middle2"),
            _make_chunk(content="last"),
        ]
        ctx = format_context(chunks)
        # BEST should appear twice (first and last)
        assert ctx.count("BEST") == 2

    def test_build_messages(self):
        msgs = build_messages("What is the policy?", "context here")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert "context here" in msgs[1]["content"]
        assert "What is the policy?" in msgs[1]["content"]
