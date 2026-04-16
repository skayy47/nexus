"""NEXUS configuration — pydantic-settings with LLM backend switch."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings

# Project root = two levels up from this file (src/nexus/config.py → nexus/)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class LLMBackend(str, Enum):
    """Supported LLM backends."""

    OLLAMA = "ollama"
    GROQ = "groq"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── LLM Backend Switch ───────────────────────────
    llm_backend: LLMBackend = LLMBackend.GROQ

    # ── Groq (hosted demo) ───────────────────────────
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # ── Ollama (local dev) ───────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # ── Supabase (pgvector) ──────────────────────────
    supabase_url: str = "http://localhost:54321"
    supabase_key: str = ""

    # ── Embeddings ───────────────────────────────────
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embed_dim: int = 384

    # ── Retrieval ────────────────────────────────────
    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_k: int = 8
    rerank_k: int = 4

    # ── API ──────────────────────────────────────────
    allowed_origins: str = "http://localhost:3000,http://localhost:8501"
    max_queries_per_session: int = 20
    demo_data_path: str = ""  # Resolved to <project_root>/demo_corpus if empty

    # ── Logging ──────────────────────────────────────
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"

    @property
    def origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def resolved_demo_data_path(self) -> Path:
        """Resolve demo_data_path relative to project root (not CWD).

        Falls back to <project_root>/demo_corpus if the setting is empty
        or the configured path is relative.
        """
        configured = self.demo_data_path.strip()
        if configured:
            p = Path(configured)
            if p.is_absolute():
                return p
            # Relative path: resolve relative to project root, not CWD
            return _PROJECT_ROOT / p
        return _PROJECT_ROOT / "demo_corpus"

    model_config = {
        "env_file": str(_ENV_FILE),
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings instance — cached after first call."""
    return Settings()
