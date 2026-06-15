"""Contradiction Radar — second LLM call to detect conflicting statements."""
import json
import re
from typing import Optional

from pydantic import BaseModel

from core.retrieval import RetrievedChunk
from core.llm import single_call


class ContradictionResult(BaseModel):
    excerpt_a: str
    excerpt_b: str
    source_a: str
    source_b: str
    explanation: str


CONTRADICTION_PROMPT = """You are analyzing document excerpts for factual contradictions.

Excerpts:
{chunks}

Do any of these excerpts contain factual contradictions with each other?
A contradiction means two excerpts make INCOMPATIBLE factual claims about the same topic.

If YES, respond with ONLY valid JSON in this exact format:
{{
  "excerpt_a": "the first conflicting statement (verbatim)",
  "excerpt_b": "the second conflicting statement (verbatim)",
  "source_a": "document name for excerpt_a",
  "source_b": "document name for excerpt_b",
  "explanation": "one sentence explaining why these conflict"
}}

If NO contradictions exist, respond with ONLY: null"""


async def detect_contradiction(chunks: list[RetrievedChunk]) -> Optional[ContradictionResult]:
    if len(chunks) < 2:
        return None

    formatted = "\n\n---\n\n".join(
        f"Source: {c.document_name}\n{c.content}" for c in chunks
    )
    prompt = CONTRADICTION_PROMPT.format(chunks=formatted)

    raw = await single_call(prompt, max_tokens=512)
    raw = raw.strip()

    if raw.lower() == "null" or not raw:
        return None

    # Extract JSON from response (model may wrap it in markdown)
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not json_match:
        return None

    try:
        data = json.loads(json_match.group())
        return ContradictionResult(**data)
    except (json.JSONDecodeError, ValueError):
        return None
