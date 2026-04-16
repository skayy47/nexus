"""Hybrid retriever — BM25 + dense search with Reciprocal Rank Fusion."""

from __future__ import annotations

from dataclasses import dataclass

import structlog

from nexus.config import get_settings
from nexus.index.bm25_index import get_bm25_index

logger = structlog.get_logger(__name__)

RRF_K = 60  # Standard RRF constant


@dataclass
class RetrievedChunk:
    """A chunk retrieved via hybrid search, with fused score."""

    chunk_id: str
    document_name: str
    page_number: int
    content: str
    section_header: str
    score: float  # Fused RRF score
    dense_score: float = 0.0  # Original semantic score
    sparse_score: float = 0.0  # Original BM25 score


async def hybrid_retrieve(
    query: str,
    query_embedding: list[float],
    k: int | None = None,
) -> list[RetrievedChunk]:
    """Hybrid retrieval: BM25 sparse + pgvector dense, fused with RRF.

    Args:
        query: The user's question text.
        query_embedding: Pre-computed embedding of the query.
        k: Number of results to return. Defaults to settings.retrieval_k.

    Returns:
        Top-k chunks sorted by fused RRF score.
        Logs retrieval scores for silent low-recall detection.
    """
    settings = get_settings()
    k = k or settings.retrieval_k

    # 1. Dense retrieval via pgvector (lazy import to avoid supabase at import time)
    from nexus.index.supabase_store import similarity_search

    dense_results = await similarity_search(query_embedding, k=k * 2)

    # 2. Sparse retrieval via BM25
    bm25_index = get_bm25_index()
    sparse_results = bm25_index.search(query, k=k * 2)

    # 3. Reciprocal Rank Fusion
    rrf_scores: dict[str, float] = {}
    dense_scores: dict[str, float] = {}
    sparse_scores: dict[str, float] = {}
    id_to_chunk: dict[str, object] = {}

    for rank, chunk in enumerate(dense_results):
        rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0) + 1 / (RRF_K + rank + 1)
        dense_scores[chunk.chunk_id] = chunk.score
        id_to_chunk[chunk.chunk_id] = chunk

    for rank, bm25_result in enumerate(sparse_results):
        chunk = bm25_result.chunk
        rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0) + 1 / (RRF_K + rank + 1)
        sparse_scores[chunk.chunk_id] = bm25_result.score
        id_to_chunk[chunk.chunk_id] = chunk

    # 4. Sort by fused score, take top-k
    top_ids = sorted(rrf_scores, key=rrf_scores.__getitem__, reverse=True)[:k]

    results = [
        RetrievedChunk(
            chunk_id=cid,
            document_name=id_to_chunk[cid].document_name,
            page_number=id_to_chunk[cid].page_number,
            content=id_to_chunk[cid].content,
            section_header=id_to_chunk[cid].section_header,
            score=rrf_scores[cid],
            dense_score=dense_scores.get(cid, 0.0),
            sparse_score=sparse_scores.get(cid, 0.0),
        )
        for cid in top_ids
    ]

    # 5. Log for silent low-recall detection
    max_score = max((r.score for r in results), default=0.0)
    if max_score < 0.01 and results:
        logger.warning(
            "Low retrieval scores detected — possible low recall",
            query=query[:100],
            max_rrf_score=max_score,
            result_count=len(results),
        )
    else:
        logger.info(
            "Hybrid retrieval complete",
            query=query[:50],
            result_count=len(results),
            max_rrf_score=round(max_score, 4),
            dense_hits=len(dense_results),
            sparse_hits=len(sparse_results),
        )

    return results
