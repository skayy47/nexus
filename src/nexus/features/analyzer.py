"""Smart Document Analyzer — summary + question suggestions on upload."""

from __future__ import annotations

import json

import structlog

logger = structlog.get_logger(__name__)

_SUMMARY_PROMPT = """\
You are analyzing a document for an institutional memory system.

Document: "{filename}"
Content excerpt (first 3000 chars):
{excerpt}

Produce a concise analysis in JSON:
{{
  "summary": "2-3 sentence overview of what this document covers",
  "key_topics": ["topic1", "topic2", "topic3"],
  "suggested_questions": [
    "A specific question this document can answer",
    "Another specific question, especially one revealing interesting data",
    "A third question — ideally one that might surface contradictions with other docs"
  ]
}}

Make the suggested_questions concrete and specific to THIS document's content.
Good: "What is the approved remote work limit per week?"
Bad: "What does this document say?"
"""


async def analyze_document(
    filename: str,
    chunks: list,
) -> tuple[str, list[str]]:
    """Generate document summary and suggested questions.

    Returns (summary, suggested_questions).
    Falls back gracefully on any LLM error.
    """
    if not chunks:
        return "", []

    # Build a representative excerpt from first 6 chunks
    excerpt = "\n\n".join(c.content[:500] for c in chunks[:6])[:3000]

    from nexus.rag.llm_client import single_call

    prompt = _SUMMARY_PROMPT.format(filename=filename, excerpt=excerpt)

    try:
        raw = await single_call(prompt, max_tokens=400, temperature=0.1)
        raw = raw.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)
        summary = data.get("summary", "")[:400]
        questions = [q[:200] for q in data.get("suggested_questions", [])[:3]]
        return summary, questions

    except Exception as e:
        logger.warning("Document analysis failed", filename=filename, error=str(e))
        return "", []
