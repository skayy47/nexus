"""Tests for nexus.config — settings, backend switch, env loading."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from nexus.config import LLMBackend, Settings, get_settings


class TestSettings:
    """Test configuration loading and validation."""

    def test_defaults(self):
        """Settings should have sensible defaults."""
        with patch.dict(os.environ, {}, clear=True):
            s = Settings(
                _env_file=None,  # Don't load .env in tests
            )
        assert s.llm_backend == LLMBackend.GROQ
        assert s.chunk_size == 800
        assert s.chunk_overlap == 120
        assert s.retrieval_k == 8
        assert s.rerank_k == 4
        assert s.embed_dim == 384
        assert s.max_queries_per_session == 20

    def test_ollama_backend(self):
        """Should switch to Ollama when LLM_BACKEND=ollama."""
        with patch.dict(os.environ, {"LLM_BACKEND": "ollama"}, clear=False):
            s = Settings(_env_file=None)
        assert s.llm_backend == LLMBackend.OLLAMA
        assert s.ollama_model == "llama3.1:8b"

    def test_groq_backend(self):
        """Should use Groq when LLM_BACKEND=groq."""
        with patch.dict(os.environ, {"LLM_BACKEND": "groq"}, clear=False):
            s = Settings(_env_file=None)
        assert s.llm_backend == LLMBackend.GROQ
        assert s.groq_model == "llama-3.3-70b-versatile"

    def test_origins_list(self):
        """Should parse comma-separated origins."""
        s = Settings(
            allowed_origins="http://a.com, http://b.com,http://c.com",
            _env_file=None,
        )
        assert s.origins_list == ["http://a.com", "http://b.com", "http://c.com"]

    def test_embed_model_pinned(self):
        """Embedding model should be pinned to all-MiniLM-L6-v2."""
        s = Settings(_env_file=None)
        assert "MiniLM" in s.embed_model
        assert s.embed_dim == 384

    def test_extra_env_vars_ignored(self):
        """Unknown env vars should not crash settings."""
        with patch.dict(os.environ, {"UNKNOWN_VAR": "value"}, clear=False):
            s = Settings(_env_file=None)
        assert s.llm_backend in (LLMBackend.GROQ, LLMBackend.OLLAMA)
