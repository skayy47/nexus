"""Hybrid retrieval: BM25 keyword + semantic vector search fused with RRF."""
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from config import get_settings
from core.embeddings import embed_query
from db.supabase_store import similarity_search, get_all_chunks

settings = get_settings()

RRF_K = 60  # standard RRF constant


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_name: str
    page_number: int
    content: str
    score: float  # fused RRF score


async def hybrid_retrieve(query: str, k: int = 6) -> list[RetrievedChunk]:
    # Semantic search via pgvector
    query_vec = embed_query(query)
    semantic_results = await similarity_search(query_vec, k=k * 2)

    # BM25 over all stored chunks (acceptable for demo-scale corpus)
    all_chunks = await get_all_chunks()
    if not all_chunks:
        return []

    tokenized = [c.content.lower().split() for c in all_chunks]
    bm25 = BM25Okapi(tokenized)
    bm25_scores = bm25.get_scores(query.lower().split())
    bm25_ranked = sorted(
        zip(all_chunks, bm25_scores), key=lambda x: x[1], reverse=True
    )[:k * 2]

    # Reciprocal Rank Fusion
    rrf_scores: dict[str, float] = {}
    id_to_chunk: dict[str, any] = {}

    for rank, result in enumerate(semantic_results):
        rrf_scores[result.chunk_id] = rrf_scores.get(result.chunk_id, 0) + 1 / (RRF_K + rank + 1)
        id_to_chunk[result.chunk_id] = result

    for rank, (chunk, _) in enumerate(bm25_ranked):
        rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0) + 1 / (RRF_K + rank + 1)
        id_to_chunk[chunk.chunk_id] = chunk

    top_ids = sorted(rrf_scores, key=rrf_scores.__getitem__, reverse=True)[:k]

    return [
        RetrievedChunk(
            chunk_id=cid,
            document_name=id_to_chunk[cid].document_name,
            page_number=id_to_chunk[cid].page_number,
            content=id_to_chunk[cid].content,
            score=rrf_scores[cid],
        )
        for cid in top_ids
    ]
