"""API routes — health, upload, chat, insights."""

from __future__ import annotations

import json
import uuid
from collections import defaultdict

import structlog
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from nexus.config import get_settings
from nexus.features.transparency import build_transparency
from nexus.index.hybrid_retriever import hybrid_retrieve
from nexus.index.supabase_store import (
    clear_all_chunks,
    delete_chunks_by_name,
    get_chunk_count,
    get_document_count,
    get_document_list,
)
from nexus.ingest.chunker import chunk_document
from nexus.ingest.loaders import load_document
from nexus.rag.chain import generate_answer
from nexus.rag.embeddings import embed_query, embed_texts

logger = structlog.get_logger(__name__)
router = APIRouter()
settings = get_settings()

# In-memory session query counter (resets on restart — acceptable for V1)
_session_counts: dict[str, int] = defaultdict(int)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


# ── Schemas ──────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    indexed_chunks: int
    llm_backend: str
    version: str


class UploadResponse(BaseModel):
    status: str
    filename: str
    chunk_count: int


class DemoResponse(BaseModel):
    status: str
    documents_loaded: int
    total_chunks: int


class DocumentEntry(BaseModel):
    name: str
    chunk_count: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentEntry]


class ChatRequest(BaseModel):
    question: str
    session_id: str = ""
    transparency_mode: bool = True


# ── Health ───────────────────────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Instant health check — never blocks on Supabase or model loading."""
    return HealthResponse(
        status="ok",
        indexed_chunks=0,
        llm_backend=settings.llm_backend.value,
        version="0.1.0",
    )


# ── Upload ───────────────────────────────────────────────────────────────────


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:  # noqa: B008
    """Upload and index a document (PDF, DOCX, MD, TXT, HTML)."""
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit.")

    filename = file.filename or "upload"

    try:
        # Load → Chunk → Embed → Store
        pages = load_document(content, filename)
        chunks = chunk_document(pages, filename)

        if not chunks:
            raise HTTPException(status_code=422, detail="No text could be extracted from file.")

        embeddings = embed_texts([c.content for c in chunks])

        from nexus.index.supabase_store import upsert_chunks

        await upsert_chunks(chunks, embeddings)

        # Rebuild BM25 index
        from nexus.index.bm25_index import get_bm25_index
        from nexus.index.supabase_store import get_all_chunks

        all_chunks = await get_all_chunks()
        get_bm25_index().build(all_chunks)

        return UploadResponse(status="ok", filename=filename, chunk_count=len(chunks))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload failed", filename=filename, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


# ── Demo ─────────────────────────────────────────────────────────────────────


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    """List all indexed documents with their chunk counts."""
    docs = await get_document_list()
    return DocumentListResponse(documents=[DocumentEntry(**d) for d in docs])


@router.delete("/documents/{document_name}")
async def delete_one_document(document_name: str):
    """Delete all chunks for a single named document and rebuild BM25."""
    deleted = await delete_chunks_by_name(document_name)

    from nexus.index.bm25_index import get_bm25_index
    from nexus.index.supabase_store import get_all_chunks

    all_chunks = await get_all_chunks()
    get_bm25_index().build(all_chunks)

    logger.info("Document deleted", document=document_name, deleted=deleted)
    return {"status": "ok", "document": document_name, "deleted": deleted}


@router.delete("/documents")
async def clear_documents():
    """Clear all indexed documents and reset the BM25 index."""
    deleted = await clear_all_chunks()

    from nexus.index.bm25_index import get_bm25_index

    get_bm25_index().build([])

    logger.info("All documents cleared", deleted=deleted)
    return {"status": "ok", "deleted": deleted}


@router.post("/demo", response_model=DemoResponse)
async def load_demo() -> DemoResponse:
    """Load the demo corpus — clears existing docs first for a clean slate."""
    await clear_all_chunks()

    demo_path = settings.resolved_demo_data_path
    if not demo_path.exists():
        raise HTTPException(status_code=404, detail="Demo corpus directory not found.")

    extensions = {".pdf", ".docx", ".md", ".txt", ".html"}
    demo_files = [f for f in demo_path.iterdir() if f.suffix.lower() in extensions]

    if not demo_files:
        raise HTTPException(status_code=404, detail="No demo files found.")

    total_chunks = 0
    for filepath in demo_files:
        try:
            content = filepath.read_bytes()
            pages = load_document(content, filepath.name)
            chunks = chunk_document(pages, filepath.name, source_path=str(filepath))
            if chunks:
                embeddings = embed_texts([c.content for c in chunks])
                from nexus.index.supabase_store import upsert_chunks

                await upsert_chunks(chunks, embeddings)
                total_chunks += len(chunks)
        except Exception as e:
            logger.error("Demo file failed", filename=filepath.name, error=str(e))
            raise HTTPException(
                status_code=500, detail=f"Failed processing {filepath.name}: {e}"
            ) from e

    # Rebuild BM25 index
    from nexus.index.bm25_index import get_bm25_index
    from nexus.index.supabase_store import get_all_chunks

    all_chunks = await get_all_chunks()
    get_bm25_index().build(all_chunks)

    return DemoResponse(status="ok", documents_loaded=len(demo_files), total_chunks=total_chunks)


# ── Chat ─────────────────────────────────────────────────────────────────────


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Chat endpoint with SSE streaming, transparency, and contradiction detection."""
    session_id = request.session_id or str(uuid.uuid4())

    if _session_counts[session_id] >= settings.max_queries_per_session:
        raise HTTPException(
            status_code=429,
            detail="Session query limit reached. Refresh to start a new session.",
        )
    _session_counts[session_id] += 1

    return StreamingResponse(
        _generate_stream(request.question, session_id, request.transparency_mode),
        media_type="text/event-stream",
        headers={"X-Session-ID": session_id},
    )


async def _generate_stream(question: str, session_id: str, transparency: bool):
    """Internal SSE generator for the chat endpoint."""
    try:
        # 1. Retrieve
        query_vec = embed_query(question)
        chunks = await hybrid_retrieve(question, query_vec, k=settings.retrieval_k)

        if not chunks:
            yield _sse("error", {"message": "No relevant documents found."})
            return

        # 2. Stream answer tokens
        answer_tokens: list[str] = []
        async for token in generate_answer(question, chunks):
            answer_tokens.append(token)
            yield _sse("token", {"text": token})

        full_answer = "".join(answer_tokens)

        # 3. Transparency (confidence + sources)
        if transparency:
            transparency_result = build_transparency(chunks)
            yield _sse("transparency", transparency_result.model_dump())

        # 4. Contradiction check (stub — Phase 2)
        from nexus.features.contradiction import detect_contradictions

        contradiction = await detect_contradictions(chunks)
        if contradiction:
            yield _sse("contradiction", contradiction.model_dump())

        # 5. Done
        yield _sse("done", {"answer": full_answer, "session_id": session_id})

    except Exception as e:
        logger.error("Chat generation failed", error=str(e), question=question[:80])
        yield _sse("error", {"message": f"Generation failed: {str(e)}"})


def _sse(event: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ── Insights (stub) ─────────────────────────────────────────────────────────


@router.get("/insights")
async def get_insights():
    """Get corpus insights — document count, contradictions, gaps."""
    return {
        "document_count": await get_document_count(),
        "contradiction_count": 0,
        "gap_count": 0,
        "top_topics": [],
    }


# ── Stats ────────────────────────────────────────────────────────────────────


@router.get("/stats")
async def get_stats():
    """Simple observability endpoint."""
    return {
        "indexed_chunks": await get_chunk_count(),
        "llm_backend": settings.llm_backend.value,
        "active_sessions": len(_session_counts),
        "total_queries": sum(_session_counts.values()),
    }
