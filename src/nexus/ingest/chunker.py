"""Metadata-aware chunker — preserves section headers, page numbers, source path."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import structlog
from langchain_text_splitters import RecursiveCharacterTextSplitter

from nexus.config import get_settings
from nexus.ingest.metadata import content_hash, extract_section_header

logger = structlog.get_logger(__name__)


@dataclass
class DocumentChunk:
    """A chunk of text with rich metadata for retrieval and attribution."""

    chunk_id: str
    content: str
    document_name: str
    page_number: int
    section_header: str
    source_path: str
    ingestion_date: str
    content_hash: str
    char_start: int = 0
    char_end: int = 0
    metadata: dict[str, str | int] = field(default_factory=dict)


def chunk_document(
    pages: list[dict[str, str | int]],
    filename: str,
    source_path: str = "",
) -> list[DocumentChunk]:
    """Split document pages into overlapping chunks with metadata.

    Args:
        pages: List of dicts with 'text' and 'page' keys (from loaders).
        filename: Original filename for attribution.
        source_path: Full path to source file.

    Returns:
        List of DocumentChunk objects ready for indexing.
    """
    settings = get_settings()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
        length_function=len,
    )

    now = datetime.now(timezone.utc).isoformat()
    chunks: list[DocumentChunk] = []

    for page_data in pages:
        text = str(page_data["text"])
        page = int(page_data.get("page", 1))

        if not text.strip():
            continue

        pieces = splitter.split_text(text)
        offset = 0

        for piece in pieces:
            c_hash = content_hash(piece)
            section = extract_section_header(piece)

            chunks.append(
                DocumentChunk(
                    chunk_id=str(uuid.uuid5(uuid.NAMESPACE_DNS, c_hash)),
                    content=piece,
                    document_name=filename,
                    page_number=page,
                    section_header=section,
                    source_path=source_path or filename,
                    ingestion_date=now,
                    content_hash=c_hash,
                    char_start=offset,
                    char_end=offset + len(piece),
                )
            )
            offset += len(piece)

    logger.info(
        "Chunked document",
        filename=filename,
        chunk_count=len(chunks),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    return chunks
