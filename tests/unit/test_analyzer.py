"""Tests for nexus.features.analyzer — Auto-Summary on Upload.

The LLM call (single_call) is mocked so tests run without API keys.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from nexus.features.analyzer import analyze_document


# ── Helpers ──────────────────────────────────────────────────────────────────


class FakeChunk:
    def __init__(self, content: str) -> None:
        self.content = content


def _make_chunks(n: int = 3) -> list[FakeChunk]:
    return [
        FakeChunk(
            f"This is chunk {i}. It describes the remote work policy that allows "
            f"employees to work from home up to 3 days per week. Budget: $500k."
        )
        for i in range(n)
    ]


def _valid_response(**overrides) -> str:
    data = {
        "one_liner": "An HR policy covering remote work limits and employee benefits.",
        "bullets": [
            "Remote work is capped at 3 days per week per the 2023 HR policy.",
            "Annual training budget set at $2,000 per employee for 2023.",
            "Parental leave extended to 16 weeks for primary caregivers.",
            "Performance reviews moved from annual to bi-annual cadence.",
        ],
        "suggested_questions": [
            "What is the maximum number of remote work days allowed per week?",
            "What is the annual training budget per employee?",
            "How long is parental leave for primary caregivers?",
        ],
    }
    data.update(overrides)
    return json.dumps(data)


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestAnalyzeDocumentEmptyInput:
    @pytest.mark.asyncio
    async def test_empty_chunks_returns_empty(self):
        one_liner, bullets, questions = await analyze_document("doc.pdf", [])
        assert one_liner == ""
        assert bullets == []
        assert questions == []


class TestAnalyzeDocumentSuccess:
    @pytest.mark.asyncio
    async def test_returns_one_liner(self):
        with patch("nexus.rag.llm_client.single_call", new_callable=AsyncMock) as mock:
            mock.return_value = _valid_response()
            one_liner, _, _ = await analyze_document("policy.pdf", _make_chunks())
        assert one_liner == "An HR policy covering remote work limits and employee benefits."

    @pytest.mark.asyncio
    async def test_returns_four_bullets(self):
        with patch("nexus.rag.llm_client.single_call", new_callable=AsyncMock) as mock:
            mock.return_value = _valid_response()
            _, bullets, _ = await analyze_document("policy.pdf", _make_chunks())
        assert len(bullets) == 4
        assert "3 days per week" in bullets[0]

    @pytest.mark.asyncio
    async def test_returns_three_questions(self):
        with patch("nexus.rag.llm_client.single_call", new_callable=AsyncMock) as mock:
            mock.return_value = _valid_response()
            _, _, questions = await analyze_document("policy.pdf", _make_chunks())
        assert len(questions) == 3
        assert all(isinstance(q, str) and len(q) > 0 for q in questions)

    @pytest.mark.asyncio
    async def test_strips_markdown_fences(self):
        fenced = "```json\n" + _valid_response() + "\n```"
        with patch("nexus.rag.llm_client.single_call", new_callable=AsyncMock) as mock:
            mock.return_value = fenced
            one_liner, bullets, questions = await analyze_document("policy.pdf", _make_chunks())
        assert one_liner != ""
        assert len(bullets) == 4
        assert len(questions) == 3

    @pytest.mark.asyncio
    async def test_truncates_long_one_liner(self):
        long_liner = "x" * 500
        with patch("nexus.rag.llm_client.single_call", new_callable=AsyncMock) as mock:
            mock.return_value = _valid_response(one_liner=long_liner)
            one_liner, _, _ = await analyze_document("policy.pdf", _make_chunks())
        assert len(one_liner) <= 200

    @pytest.mark.asyncio
    async def test_truncates_long_bullets(self):
        long_bullet = "y" * 500
        with patch("nexus.rag.llm_client.single_call", new_callable=AsyncMock) as mock:
            mock.return_value = _valid_response(bullets=[long_bullet] * 4)
            _, bullets, _ = await analyze_document("policy.pdf", _make_chunks())
        assert all(len(b) <= 200 for b in bullets)

    @pytest.mark.asyncio
    async def test_caps_bullets_at_four(self):
        extra_bullets = [f"Bullet {i}" for i in range(10)]
        with patch("nexus.rag.llm_client.single_call", new_callable=AsyncMock) as mock:
            mock.return_value = _valid_response(bullets=extra_bullets)
            _, bullets, _ = await analyze_document("policy.pdf", _make_chunks())
        assert len(bullets) <= 4

    @pytest.mark.asyncio
    async def test_caps_questions_at_three(self):
        extra_qs = [f"Question {i}?" for i in range(10)]
        with patch("nexus.rag.llm_client.single_call", new_callable=AsyncMock) as mock:
            mock.return_value = _valid_response(suggested_questions=extra_qs)
            _, _, questions = await analyze_document("policy.pdf", _make_chunks())
        assert len(questions) <= 3

    @pytest.mark.asyncio
    async def test_single_chunk_works(self):
        with patch("nexus.rag.llm_client.single_call", new_callable=AsyncMock) as mock:
            mock.return_value = _valid_response()
            one_liner, bullets, questions = await analyze_document("doc.pdf", _make_chunks(1))
        assert one_liner != ""
        assert len(bullets) > 0

    @pytest.mark.asyncio
    async def test_uses_up_to_six_chunks_for_excerpt(self):
        chunks = _make_chunks(20)
        captured_prompt: list[str] = []

        async def capture(prompt, **_kwargs):
            captured_prompt.append(prompt)
            return _valid_response()

        with patch("nexus.rag.llm_client.single_call", new=capture):
            await analyze_document("big.pdf", chunks)

        # First 6 chunks × 500 chars = 3000 max chars in prompt
        assert "chunk 0" in captured_prompt[0]
        assert "chunk 6" not in captured_prompt[0]


class TestAnalyzeDocumentFallback:
    @pytest.mark.asyncio
    async def test_llm_error_returns_empty(self):
        with patch("nexus.rag.llm_client.single_call", new_callable=AsyncMock) as mock:
            mock.side_effect = RuntimeError("LLM timeout")
            one_liner, bullets, questions = await analyze_document("policy.pdf", _make_chunks())
        assert one_liner == ""
        assert bullets == []
        assert questions == []

    @pytest.mark.asyncio
    async def test_invalid_json_returns_empty(self):
        with patch("nexus.rag.llm_client.single_call", new_callable=AsyncMock) as mock:
            mock.return_value = "not json at all"
            one_liner, bullets, questions = await analyze_document("policy.pdf", _make_chunks())
        assert one_liner == ""
        assert bullets == []
        assert questions == []

    @pytest.mark.asyncio
    async def test_partial_json_missing_bullets_returns_empty_list(self):
        partial = json.dumps({"one_liner": "A document about stuff."})
        with patch("nexus.rag.llm_client.single_call", new_callable=AsyncMock) as mock:
            mock.return_value = partial
            one_liner, bullets, questions = await analyze_document("policy.pdf", _make_chunks())
        assert one_liner == "A document about stuff."
        assert bullets == []
        assert questions == []
