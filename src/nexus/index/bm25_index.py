"""BM25 keyword search index — cached, rebuilt on ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import structlog
from rank_bm25 import BM25Okapi

logger = structlog.get_logger(__name__)


class ChunkLike(Protocol):
    """Protocol for any object that has chunk_id, document_name, page_number, content."""

    chunk_id: str
    document_name: str
    page_number: int
    content: str
    section_header: str


@dataclass
class BM25Result:
    """BM25 search result with score."""

    chunk: ChunkLike
    score: float


class BM25Index:
    """Cached BM25 index over the corpus.

    Rebuilt when new documents are ingested.
    For demo scale (<1000 chunks), this is fast enough.
    """

    def __init__(self) -> None:
        self._index: BM25Okapi | None = None
        self._chunks: list[ChunkLike] = []
        self._is_built = False

    def build(self, chunks: list[ChunkLike]) -> None:
        """Build (or rebuild) the BM25 index from chunks."""
        if not chunks:
            self._index = None
            self._chunks = []
            self._is_built = False
            return

        self._chunks = chunks
        tokenized = [c.content.lower().split() for c in chunks]
        self._index = BM25Okapi(tokenized)
        self._is_built = True
        logger.info("BM25 index built", chunk_count=len(chunks))

    @property
    def is_built(self) -> bool:
        return self._is_built

    def search(self, query: str, k: int = 12) -> list[BM25Result]:
        """Search the BM25 index. Returns top-k results with scores."""
        if not self._is_built or self._index is None:
            return []

        query_tokens = query.lower().split()
        scores = self._index.get_scores(query_tokens)

        scored = sorted(
            zip(self._chunks, scores, strict=False),
            key=lambda x: x[1],
            reverse=True,
        )

        return [BM25Result(chunk=chunk, score=float(score)) for chunk, score in scored[:k]]


# Module-level singleton — rebuilt when corpus changes
_bm25_index = BM25Index()


def get_bm25_index() -> BM25Index:
    """Get the global BM25 index singleton."""
    return _bm25_index
