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
        assert PROMPT_VERSION == "v2"

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

    def test_build_messages_french_hint(self):
        """French locale must inject the French response directive."""
        msgs = build_messages("Quelle est la politique ?", "contexte ici", language="fr")
        user_content = msgs[1]["content"]
        assert "Répondez en français" in user_content

    def test_build_messages_english_hint(self):
        """English locale must inject the English response directive."""
        msgs = build_messages("What is the policy?", "context here", language="en")
        user_content = msgs[1]["content"]
        assert "respond in English" in user_content

    def test_build_messages_unknown_locale_no_hint(self):
        """Unknown locale should not inject any directive."""
        msgs = build_messages("¿Cuál es la política?", "contexto", language="es")
        user_content = msgs[1]["content"]
        assert "Répondez" not in user_content
        assert "respond in English" not in user_content
