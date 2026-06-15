from functools import lru_cache

from sentence_transformers import SentenceTransformer

from config import get_settings

settings = get_settings()


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Singleton — loaded once on startup, shared across all requests."""
    return SentenceTransformer(settings.embed_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    return model.encode(texts, batch_size=32, show_progress_bar=False).tolist()


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
