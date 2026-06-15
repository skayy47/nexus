import io
import uuid
from dataclasses import dataclass

from langchain.text_splitter import RecursiveCharacterTextSplitter
from unstructured.partition.auto import partition

from config import get_settings

settings = get_settings()


@dataclass
class DocumentChunk:
    chunk_id: str
    document_name: str
    page_number: int
    content: str
    char_start: int
    char_end: int


async def ingest_file(content: bytes, filename: str) -> list[DocumentChunk]:
    """Parse a PDF/DOCX file and return overlapping text chunks."""
    elements = partition(file=io.BytesIO(content), content_type=_mime(filename))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ".", " "],
    )

    chunks: list[DocumentChunk] = []
    for element in elements:
        text = str(element).strip()
        if not text:
            continue
        page = getattr(element.metadata, "page_number", 1) or 1
        pieces = splitter.split_text(text)
        offset = 0
        for piece in pieces:
            chunks.append(DocumentChunk(
                chunk_id=str(uuid.uuid4()),
                document_name=filename,
                page_number=page,
                content=piece,
                char_start=offset,
                char_end=offset + len(piece),
            ))
            offset += len(piece)

    return chunks


def _mime(filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        return "application/pdf"
    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
