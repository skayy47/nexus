"""Metadata extraction utilities — section headers, content hashing."""

from __future__ import annotations

import hashlib
import re


def content_hash(text: str) -> str:
    """Generate a deterministic hash for deduplication.

    Uses SHA-256 truncated to 32 chars for readability while
    maintaining collision resistance.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]


def extract_section_header(text: str) -> str:
    """Extract the most likely section header from a chunk of text.

    Looks for common header patterns: markdown headers, ALL CAPS lines,
    numbered sections.
    """
    lines = text.strip().split("\n")

    for line in lines[:3]:  # Check first 3 lines
        line = line.strip()
        if not line:
            continue

        # Markdown headers: # Header, ## Header, ### Header
        md_match = re.match(r"^#{1,4}\s+(.+)$", line)
        if md_match:
            return md_match.group(1).strip()

        # ALL CAPS headers (common in policy docs)
        if line.isupper() and 3 < len(line) < 80:
            return line.title()

        # Numbered sections: 1. Header, 1.1 Header, Section 1:
        num_match = re.match(r"^(?:Section\s+)?\d+(?:\.\d+)*[.:]\s*(.+)$", line, re.IGNORECASE)
        if num_match:
            return num_match.group(1).strip()

    return ""
