"""Supabase pgvector store — upsert chunks and similarity search."""
import uuid
from dataclasses import dataclass

from supabase import acreate_client, AsyncClient

from config import get_settings
from core.embeddings import embed_texts

settings = get_settings()

_client: AsyncClient | None = None


async def _get_client() -> AsyncClient:
    global _client
    if _client is None:
        _client = await acreate_client(settings.supabase_url, settings.supabase_key)
    return _client


@dataclass
class StoredChunk:
    chunk_id: str
    document_name: str
    page_number: int
    content: str


async def upsert_chunks(chunks) -> str:
    """Embed and upsert a list of DocumentChunk objects. Returns a document_id."""
    from core.ingestion import DocumentChunk
    client = await _get_client()

    doc_id = str(uuid.uuid4())
    texts = [c.content for c in chunks]
    embeddings = embed_texts(texts)

    rows = [
        {
            "id": c.chunk_id,
            "document_id": doc_id,
            "document_name": c.document_name,
            "page_number": c.page_number,
            "content": c.content,
            "embedding": emb,
        }
        for c, emb in zip(chunks, embeddings)
    ]

    await client.table("document_chunks").upsert(rows).execute()
    return doc_id


async def similarity_search(query_vec: list[float], k: int = 12) -> list[StoredChunk]:
    """Top-k cosine similarity search via pgvector RPC."""
    client = await _get_client()

    result = await client.rpc(
        "match_chunks",
        {"query_embedding": query_vec, "match_count": k},
    ).execute()

    return [
        StoredChunk(
            chunk_id=row["id"],
            document_name=row["document_name"],
            page_number=row["page_number"],
            content=row["content"],
        )
        for row in (result.data or [])
    ]


async def get_all_chunks() -> list[StoredChunk]:
    """Fetch all chunks for BM25 indexing (demo-scale corpus only)."""
    client = await _get_client()
    result = await client.table("document_chunks").select("id,document_name,page_number,content").execute()
    return [
        StoredChunk(
            chunk_id=row["id"],
            document_name=row["document_name"],
            page_number=row["page_number"],
            content=row["content"],
        )
        for row in (result.data or [])
    ]
