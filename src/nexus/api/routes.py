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
from nexus.features.transparency import build_grounding
from nexus.index.hybrid_retriever import hybrid_retrieve
from nexus.index.supabase_store import (
    clear_all_chunks,
    delete_chunks_by_name,
    get_chunk_count,
    get_document_count,
    get_document_list,
)
from nexus.ingest.chunker import chunk_document
from nexus.ingest.loaders import SUPPORTED_EXTENSIONS, load_document
from nexus.rag.chain import generate_answer
from nexus.rag.embeddings import embed_query, embed_texts

logger = structlog.get_logger(__name__)
router = APIRouter()
settings = get_settings()

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB

# In-memory session state (resets on restart — acceptable for V1)
_session_counts: dict[str, int] = defaultdict(int)
_session_gaps: dict[str, list[dict]] = defaultdict(list)  # session_id → gap list
_corpus_contradictions: list[dict] = []  # accumulated contradictions from uploads


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
    summary: str = ""
    bullets: list[str] = []
    suggested_questions: list[str] = []


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
    language: str = "en"  # UI locale ("en" | "fr") — drives the answer language


# ── Health ───────────────────────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    # Report the real indexed-chunk count; never let a DB hiccup fail the probe.
    try:
        indexed_chunks = await get_chunk_count()
    except Exception as e:
        logger.warning("Health chunk count failed", error=str(e))
        indexed_chunks = 0
    return HealthResponse(
        status="ok",
        indexed_chunks=indexed_chunks,
        llm_backend=settings.llm_backend.value,
        version="0.1.0",
    )


# ── Upload ───────────────────────────────────────────────────────────────────


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:  # noqa: B008
    """Upload and index a document. Supports PDF, DOCX, XLSX, PPTX, CSV, RTF, JSON, EML, TXT, MD, HTML."""
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 200 MB limit.")

    filename = file.filename or "upload"

    try:
        pages = load_document(content, filename)
        chunks = chunk_document(pages, filename)

        if not chunks:
            raise HTTPException(status_code=422, detail="No text could be extracted from file.")

        embeddings = embed_texts([c.content for c in chunks])

        from nexus.index.supabase_store import upsert_chunks

        await upsert_chunks(chunks, embeddings)

        # Rebuild BM25
        from nexus.index.bm25_index import get_bm25_index
        from nexus.index.supabase_store import get_all_chunks

        all_chunks = await get_all_chunks()
        get_bm25_index().build(all_chunks)

        # Smart analysis: one-liner + bullets + question suggestions
        summary = ""
        bullets: list[str] = []
        suggested_questions: list[str] = []
        try:
            from nexus.features.analyzer import analyze_document
            summary, bullets, suggested_questions = await analyze_document(filename, chunks)
        except Exception as e:
            logger.warning("Document analysis skipped", error=str(e))

        # Background: scan new doc against existing for contradictions
        try:
            await _scan_upload_contradictions(filename, all_chunks)
        except Exception as e:
            logger.warning("Contradiction scan skipped", error=str(e))

        return UploadResponse(
            status="ok",
            filename=filename,
            chunk_count=len(chunks),
            summary=summary,
            bullets=bullets,
            suggested_questions=suggested_questions,
        )
    except HTTPException:
        raise
    except ValueError as e:
        # User-facing errors: unsupported type, bad content, encrypted PDF, etc.
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Upload failed", filename=filename, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _scan_upload_contradictions(new_doc: str, all_chunks: list) -> None:
    """Scan newly uploaded doc against existing docs for contradictions."""
    global _corpus_contradictions

    # Get chunks from the new doc and from other docs
    new_chunks = [c for c in all_chunks if c.document_name == new_doc]
    other_chunks = [c for c in all_chunks if c.document_name != new_doc]

    if not new_chunks or not other_chunks:
        return

    # Sample: 4 chunks from new doc + 4 from other docs
    sample = new_chunks[:4] + other_chunks[:4]

    from nexus.features.contradiction import detect_contradictions
    from nexus.index.hybrid_retriever import RetrievedChunk

    # Convert to RetrievedChunk format
    retrieved = [
        RetrievedChunk(
            chunk_id=c.chunk_id if hasattr(c, "chunk_id") else c.get("id", ""),
            document_name=c.document_name if hasattr(c, "document_name") else c.get("document_name", ""),
            page_number=c.page_number if hasattr(c, "page_number") else c.get("page_number", 1),
            content=c.content if hasattr(c, "content") else c.get("content", ""),
            section_header=c.section_header if hasattr(c, "section_header") else c.get("section_header", ""),
            score=1.0,
        )
        for c in sample
    ]

    result = await detect_contradictions(retrieved)
    if result:
        _corpus_contradictions.append(result.model_dump())
        logger.info(
            "Corpus contradiction detected",
            source_a=result.source_a,
            source_b=result.source_b,
        )


# ── Documents ─────────────────────────────────────────────────────────────────


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    docs = await get_document_list()
    return DocumentListResponse(documents=[DocumentEntry(**d) for d in docs])


@router.delete("/documents/{document_name}")
async def delete_one_document(document_name: str):
    deleted = await delete_chunks_by_name(document_name)

    from nexus.index.bm25_index import get_bm25_index
    from nexus.index.supabase_store import get_all_chunks

    all_chunks = await get_all_chunks()
    get_bm25_index().build(all_chunks)

    # Remove any contradictions involving this document
    global _corpus_contradictions
    _corpus_contradictions = [
        c for c in _corpus_contradictions
        if c.get("source_a") != document_name and c.get("source_b") != document_name
    ]

    logger.info("Document deleted", document=document_name, deleted=deleted)
    return {"status": "ok", "document": document_name, "deleted": deleted}


@router.delete("/documents")
async def clear_documents():
    deleted = await clear_all_chunks()

    from nexus.index.bm25_index import get_bm25_index

    get_bm25_index().build([])
    _corpus_contradictions.clear()

    logger.info("All documents cleared", deleted=deleted)
    return {"status": "ok", "deleted": deleted}


# ── Demo ─────────────────────────────────────────────────────────────────────


@router.post("/demo", response_model=DemoResponse)
async def load_demo() -> DemoResponse:
    """Load the demo corpus — clears existing docs first."""
    await clear_all_chunks()
    _corpus_contradictions.clear()

    demo_path = settings.resolved_demo_data_path
    if not demo_path.exists():
        raise HTTPException(status_code=404, detail="Demo corpus directory not found.")

    extensions = set(SUPPORTED_EXTENSIONS)
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

    from nexus.index.bm25_index import get_bm25_index
    from nexus.index.supabase_store import get_all_chunks

    all_chunks = await get_all_chunks()
    get_bm25_index().build(all_chunks)

    # Scan demo corpus for contradictions
    try:
        await _scan_upload_contradictions(demo_files[-1].name, all_chunks)
    except Exception:
        pass

    return DemoResponse(status="ok", documents_loaded=len(demo_files), total_chunks=total_chunks)


# ── Chat ─────────────────────────────────────────────────────────────────────


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    session_id = request.session_id or str(uuid.uuid4())

    if _session_counts[session_id] >= settings.max_queries_per_session:
        raise HTTPException(
            status_code=429,
            detail="Session query limit reached. Refresh to start a new session.",
        )
    _session_counts[session_id] += 1

    return StreamingResponse(
        _generate_stream(
            request.question, session_id, request.transparency_mode, request.language
        ),
        media_type="text/event-stream",
        headers={
            "X-Session-ID": session_id,
            "X-Accel-Buffering": "no",   # disable nginx proxy buffering
            "Cache-Control": "no-cache",
        },
    )


async def _generate_stream(
    question: str, session_id: str, transparency: bool, language: str = "en"
):
    try:
        # Ping immediately so nginx/HF-Spaces proxy doesn't buffer the connection.
        yield ": ping\n\n"

        query_vec = embed_query(question)
        chunks = await hybrid_retrieve(question, query_vec, k=settings.retrieval_k)

        if not chunks:
            yield _sse("error", {"message": "No relevant documents found."})
            return

        # Stream answer tokens
        answer_tokens: list[str] = []
        async for token in generate_answer(question, chunks, language):
            answer_tokens.append(token)
            yield _sse("token", {"text": token})

        full_answer = "".join(answer_tokens)

        # Guard: if the model returned nothing, surface a user-facing error
        if not full_answer.strip():
            empty_msg = (
                "Le modèle n'a pas pu générer de réponse. Veuillez réessayer."
                if (language or "en").strip().lower().startswith("fr")
                else "The model returned an empty response. Please try again."
            )
            yield _sse("error", {"message": empty_msg})
            return

        # Transparency — grounding / source verification of the generated answer
        if transparency:
            grounding = build_grounding(full_answer, chunks)
            yield _sse("grounding", grounding.model_dump())

            # Knowledge Gap detection — only fires when grounding coverage is low
            # AND the answer itself signals it couldn't find the information.
            # Prevents false gaps when NEXUS produced a well-grounded answer.
            if grounding.coverage < 0.45 and _answer_is_non_answer(full_answer):
                try:
                    from nexus.features.gap_detector import detect_gaps
                    from nexus.index.supabase_store import get_document_list

                    docs = await get_document_list()
                    doc_names = [d["name"] for d in docs]
                    gap = await detect_gaps(question, grounding.coverage, doc_names, language)
                    if gap:
                        _session_gaps[session_id].append(gap.model_dump())
                        yield _sse("gap", gap.model_dump())
                except Exception as e:
                    logger.warning("Gap detection skipped in stream", error=str(e))

        # Contradiction check
        from nexus.features.contradiction import detect_contradictions

        contradiction = await detect_contradictions(chunks, language)
        if contradiction:
            yield _sse("contradiction", contradiction.model_dump())

        yield _sse("done", {"answer": full_answer, "session_id": session_id})

    except Exception as e:
        logger.error("Chat generation failed", error=str(e), question=question[:80])
        yield _sse("error", {"message": f"Generation failed: {str(e)}"})


def _answer_is_non_answer(text: str) -> bool:
    """Return True if the answer signals it couldn't find the information.
    Used to suppress false knowledge-gap events when NEXUS actually found a good answer."""
    low = text.lower()
    signals = (
        "cannot determine", "cannot find", "i cannot", "i can't",
        "not available", "no information", "no mention", "no relevant",
        "do not contain", "does not contain", "do not mention", "does not mention",
        "not mentioned", "not provided", "not documented", "not found",
        "based on the available documents, i cannot",
        "the documents do not", "the document does not",
        "no relevant information", "unable to determine",
        # French
        "je ne peux pas", "je ne trouve pas", "aucune information",
        "non mentionné", "ne mentionne pas", "ne mentionnent pas",
        "ne contient pas", "ne contiennent pas", "non disponible",
        "impossible de déterminer", "aucune mention", "non documenté",
        "pas trouvé", "aucune information pertinente", "les documents ne",
    )
    return any(s in low for s in signals)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ── Insights ─────────────────────────────────────────────────────────────────


@router.get("/insights")
async def get_insights():
    """Corpus insights — document count, contradictions (corpus + session), knowledge gaps."""
    # Count unique gaps across all sessions
    total_gaps = sum(len(v) for v in _session_gaps.values())
    unique_gaps = len({g["topic"] for gaps in _session_gaps.values() for g in gaps})

    return {
        "document_count": await get_document_count(),
        "contradiction_count": len(_corpus_contradictions),
        "gap_count": unique_gaps,
        "corpus_contradictions": _corpus_contradictions[:5],  # top 5 for UI
        "top_topics": [],
    }


@router.get("/insights/gaps")
async def get_gaps():
    """All accumulated knowledge gaps across sessions."""
    all_gaps = [g for gaps in _session_gaps.values() for g in gaps]
    # Deduplicate by topic
    seen: set[str] = set()
    unique = []
    for g in all_gaps:
        if g["topic"] not in seen:
            seen.add(g["topic"])
            unique.append(g)
    return {"gaps": unique[:20]}


# ── Stats ─────────────────────────────────────────────────────────────────────


@router.get("/stats")
async def get_stats():
    return {
        "indexed_chunks": await get_chunk_count(),
        "llm_backend": settings.llm_backend.value,
        "active_sessions": len(_session_counts),
        "total_queries": sum(_session_counts.values()),
        "corpus_contradictions": len(_corpus_contradictions),
        "supported_formats": SUPPORTED_EXTENSIONS,
    }
