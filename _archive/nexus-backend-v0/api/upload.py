import os
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from config import get_settings
from core.ingestion import ingest_file
from db.supabase_store import upsert_chunks

router = APIRouter(tags=["upload"])
settings = get_settings()

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


class UploadResponse(BaseModel):
    status: str
    document_id: str
    chunk_count: int


class DemoResponse(BaseModel):
    status: str
    documents_loaded: int
    chunk_count: int


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    if file.content_type not in ("application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
        raise HTTPException(status_code=415, detail="Only PDF and DOCX files are supported.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit.")

    try:
        chunks = await ingest_file(content, filename=file.filename or "upload")
        doc_id = await upsert_chunks(chunks)
        return UploadResponse(status="ok", document_id=doc_id, chunk_count=len(chunks))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo", response_model=DemoResponse)
async def load_demo() -> DemoResponse:
    demo_path = Path(settings.demo_data_path)
    if not demo_path.exists():
        raise HTTPException(status_code=404, detail="Demo data directory not found.")

    demo_files = list(demo_path.glob("*.pdf")) + list(demo_path.glob("*.docx"))
    if not demo_files:
        raise HTTPException(status_code=404, detail="No demo files found.")

    total_chunks = 0
    for filepath in demo_files:
        try:
            content = filepath.read_bytes()
            chunks = await ingest_file(content, filename=filepath.name)
            await upsert_chunks(chunks)
            total_chunks += len(chunks)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed processing {filepath.name}: {e}")

    return DemoResponse(status="ok", documents_loaded=len(demo_files), chunk_count=total_chunks)
