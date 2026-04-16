"""Embeddings module — sentence-transformers with singleton pattern."""

from __future__ import annotations

from functools import lru_cache

import structlog
from sentence_transformers import SentenceTransformer

from nexus.config import get_settings

logger = structlog.get_logger(__name__)


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Singleton embedding model — loaded once on startup, shared across requests.

    Model version is pinned in config. Changing the model requires re-embedding
    the entire corpus (a migration, not a silent change).
    """
    settings = get_settings()
    model_name = settings.embed_model.replace("sentence-transformers/", "")
    logger.info("Loading embedding model", model=model_name, dim=settings.embed_dim)
    return SentenceTransformer(model_name)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts.

    Returns list of embedding vectors (each of dimension embed_dim).
    """
    model = get_embedder()
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    return embed_texts([query])[0]
