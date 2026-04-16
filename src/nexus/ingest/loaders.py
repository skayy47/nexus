"""Document loaders — PDF, DOCX, Markdown, TXT, HTML."""

from __future__ import annotations

import io
import re
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# ── Prompt Injection Detection ───────────────────────────────────────────────
_INJECTION_PATTERNS = re.compile(
    r"(ignore\s+(all\s+)?previous\s+instructions"
    r"|you\s+are\s+now\s+a"
    r"|system\s*:\s*"
    r"|<\s*system\s*>"
    r"|IMPORTANT:\s*disregard)",
    re.IGNORECASE,
)


def sniff_injection(text: str) -> bool:
    """Check text for common prompt injection patterns.

    Returns True if suspicious patterns are found.
    """
    return bool(_INJECTION_PATTERNS.search(text))


# ── Individual Loaders ───────────────────────────────────────────────────────


def load_pdf(content: bytes, filename: str) -> list[dict[str, str | int]]:
    """Load PDF using pypdf. Returns list of {text, page} dicts.

    Falls back to Unstructured for scanned/complex PDFs.
    """
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages: list[dict[str, str | int]] = []

    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"text": text, "page": i})

    if not pages:
        logger.info("pypdf extracted no text, falling back to Unstructured", filename=filename)
        return _load_with_unstructured(content, filename)

    return pages


def _load_with_unstructured(content: bytes, filename: str) -> list[dict[str, str | int]]:
    """Fallback loader using Unstructured for scanned/complex files."""
    from unstructured.partition.auto import partition

    elements = partition(file=io.BytesIO(content), content_type=_mime_type(filename))
    pages: list[dict[str, str | int]] = []

    for element in elements:
        text = str(element).strip()
        if not text:
            continue
        page = getattr(element.metadata, "page_number", 1) or 1
        pages.append({"text": text, "page": page})

    return pages


def load_docx(content: bytes, filename: str) -> list[dict[str, str | int]]:
    """Load DOCX using python-docx."""
    from docx import Document

    doc = Document(io.BytesIO(content))
    paragraphs: list[dict[str, str | int]] = []

    for _i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if text:
            paragraphs.append({"text": text, "page": 1})  # DOCX has no native pages

    return paragraphs


def load_markdown(content: bytes, filename: str) -> list[dict[str, str | int]]:
    """Load Markdown file as plain text."""
    text = content.decode("utf-8", errors="replace")
    return [{"text": text, "page": 1}] if text.strip() else []


def load_txt(content: bytes, filename: str) -> list[dict[str, str | int]]:
    """Load plain text file."""
    text = content.decode("utf-8", errors="replace")
    return [{"text": text, "page": 1}] if text.strip() else []


def load_html(content: bytes, filename: str) -> list[dict[str, str | int]]:
    """Load HTML file, stripping tags to extract text."""
    text = content.decode("utf-8", errors="replace")
    # Simple tag stripping — Unstructured handles complex HTML
    import re as _re

    clean = _re.sub(r"<[^>]+>", " ", text)
    clean = _re.sub(r"\s+", " ", clean).strip()
    return [{"text": clean, "page": 1}] if clean else []


# ── Unified Loader ──────────────────────────────────────────────────────────


_LOADER_MAP = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".md": load_markdown,
    ".txt": load_txt,
    ".html": load_html,
    ".htm": load_html,
}


def load_document(content: bytes, filename: str) -> list[dict[str, str | int]]:
    """Load a document based on file extension.

    Returns list of dicts with 'text' and 'page' keys.
    Runs prompt injection detection on each extracted text block.
    """
    ext = Path(filename).suffix.lower()
    loader = _LOADER_MAP.get(ext)

    if loader is None:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {list(_LOADER_MAP.keys())}")

    pages = loader(content, filename)

    # Check for prompt injection in loaded content
    for page_data in pages:
        text = str(page_data["text"])
        if sniff_injection(text):
            logger.warning(
                "Potential prompt injection detected in document",
                filename=filename,
                page=page_data.get("page"),
            )

    return pages


def _mime_type(filename: str) -> str:
    """Map filename to MIME type for Unstructured."""
    ext = Path(filename).suffix.lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".html": "text/html",
        ".htm": "text/html",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }
    return mime_map.get(ext, "application/octet-stream")
