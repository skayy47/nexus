"""Supabase pgvector store — upsert chunks and similarity search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog
from supabase import AsyncClient, acreate_client

from nexus.config import get_settings

if TYPE_CHECKING:
    from nexus.ingest.chunker import DocumentChunk

logger = structlog.get_logger(__name__)

_client: AsyncClient | None = None


async def _get_client() -> AsyncClient:
    """Lazy singleton for async Supabase client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = await acreate_client(settings.supabase_url, settings.supabase_key)
    return _client


@dataclass
class StoredChunk:
    """A chunk as stored in the database."""

    chunk_id: str
    document_name: str
    page_number: int
    content: str
    section_header: str = ""
    score: float = 0.0


async def upsert_chunks(
    chunks: list[DocumentChunk],
    embeddings: list[list[float]],
) -> int:
    """Upsert chunks with embeddings into pgvector.

    Uses deterministic chunk_id (content-hash based) for idempotent upserts.

    Returns:
        Number of chunks upserted.
    """
    client = await _get_client()

    rows = [
        {
            "id": chunk.chunk_id,
            "document_name": chunk.document_name,
            "page_number": chunk.page_number,
            "content": chunk.content,
            "section_header": chunk.section_header,
            "source_path": chunk.source_path,
            "ingestion_date": chunk.ingestion_date,
            "content_hash": chunk.content_hash,
            "embedding": emb,
            "metadata": {
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
            },
        }
        for chunk, emb in zip(chunks, embeddings, strict=False)
    ]

    # Upsert in batches of 100 to avoid payload limits
    batch_size = 100
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        await client.table("document_chunks").upsert(batch).execute()
        total += len(batch)

    logger.info("Upserted chunks", count=total, document=chunks[0].document_name if chunks else "")
    return total


async def similarity_search(
    query_embedding: list[float],
    k: int = 12,
) -> list[StoredChunk]:
    """Top-k cosine similarity search via pgvector RPC function.

    The RPC function 'match_chunks' must be created in Supabase — see migrations.
    """
    client = await _get_client()

    result = await client.rpc(
        "match_chunks",
        {"query_embedding": query_embedding, "match_count": k},
    ).execute()

    return [
        StoredChunk(
            chunk_id=row["id"],
            document_name=row["document_name"],
            page_number=row["page_number"],
            content=row["content"],
            section_header=row.get("section_header", ""),
            score=row.get("similarity", 0.0),
        )
        for row in (result.data or [])
    ]


async def get_all_chunks() -> list[StoredChunk]:
    """Fetch all chunks for BM25 indexing.

    Note: Only viable for demo-scale corpus (<1000 chunks).
    For production, cache the BM25 index and rebuild on ingestion.
    """
    client = await _get_client()
    result = (
        await client.table("document_chunks")
        .select("id,document_name,page_number,content,section_header")
        .execute()
    )

    return [
        StoredChunk(
            chunk_id=row["id"],
            document_name=row["document_name"],
            page_number=row["page_number"],
            content=row["content"],
            section_header=row.get("section_header", ""),
        )
        for row in (result.data or [])
    ]


async def get_chunk_count() -> int:
    """Get total number of indexed chunks."""
    client = await _get_client()
    result = await client.table("document_chunks").select("id", count="exact").execute()
    return result.count or 0


async def get_document_count() -> int:
    """Get number of unique documents indexed."""
    client = await _get_client()
    result = await client.table("document_chunks").select("document_name").execute()
    names = {row["document_name"] for row in (result.data or [])}
    return len(names)


async def get_document_list() -> list[dict[str, str | int]]:
    """Return unique documents with their chunk counts, sorted by name."""
    client = await _get_client()
    result = await client.table("document_chunks").select("document_name").execute()
    counts: dict[str, int] = {}
    for row in result.data or []:
        counts[row["document_name"]] = counts.get(row["document_name"], 0) + 1
    return [{"name": n, "chunk_count": c} for n, c in sorted(counts.items())]


async def delete_chunks_by_name(document_name: str) -> int:
    """Delete all chunks for a specific document. Returns number deleted."""
    client = await _get_client()
    result = (
        await client.table("document_chunks").delete().eq("document_name", document_name).execute()
    )
    return len(result.data or [])


async def clear_all_chunks() -> int:
    """Delete all chunks from the store. Returns number of rows deleted."""
    client = await _get_client()
    # Supabase requires a filter — neq on a UUID that never exists matches all rows
    result = (
        await client.table("document_chunks")
        .delete()
        .neq("id", "00000000-0000-0000-0000-000000000000")
        .execute()
    )
    return len(result.data or [])
