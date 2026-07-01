"""Smart Document Analyzer — one-liner, bullet-point summary + question suggestions on upload."""

from __future__ import annotations

import json
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

_LANG_INSTRUCTION = {
    "fr": "IMPORTANT: Respond entirely in French. All values in the JSON must be written in French.",
    "en": "",
}

_SUMMARY_PROMPT = """\
You are analyzing a document for an institutional memory system.
{lang_instruction}

Document: "{filename}"
Content excerpt (first 3000 chars):
{excerpt}

Produce a concise analysis in JSON with exactly these keys:
{{
  "one_liner": "One sentence (max 15 words) capturing what this document is about.",
  "bullets": [
    "Specific key fact, policy, or insight from this document (10-20 words)",
    "Another specific data point or decision found in this document (10-20 words)",
    "A third concrete takeaway — a number, rule, or conclusion (10-20 words)",
    "A fourth relevant detail that would surprise or inform a reader (10-20 words)"
  ],
  "suggested_questions": [
    "A specific question this document can answer",
    "Another specific question, especially one revealing interesting data or policy",
    "A third question that might surface contradictions with other documents"
  ]
}}

Rules:
- bullets must have exactly 4 items, each 10-20 words, specific to THIS document.
- suggested_questions must have exactly 3 items, concrete and answerable from this document.
- Good bullet: "Remote work is capped at 3 days per week per the 2023 HR policy update."
- Bad bullet: "This document covers company policies." (too vague)
- Return only valid JSON, no markdown fences.
"""


async def analyze_document(
    filename: str,
    chunks: list[Any],
    locale: str = "en",
) -> tuple[str, list[str], list[str]]:
    """Generate a one-liner, 4 bullet-point summary, and 3 suggested questions.

    Returns (one_liner, bullets, suggested_questions).
    Falls back gracefully on any LLM error.
    """
    if not chunks:
        return "", [], []

    excerpt = "\n\n".join(c.content[:500] for c in chunks[:6])[:3000]

    from nexus.rag.llm_client import single_call

    lang_instruction = _LANG_INSTRUCTION.get(locale, "")
    prompt = _SUMMARY_PROMPT.format(
        filename=filename, excerpt=excerpt, lang_instruction=lang_instruction
    )

    try:
        raw = await single_call(prompt, max_tokens=600, temperature=0.1)
        raw = raw.strip()

        # Strip markdown fences if the LLM added them anyway
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else parts[0]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)
        one_liner = str(data.get("one_liner", ""))[:200]
        bullets = [str(b)[:200] for b in data.get("bullets", [])[:4]]
        questions = [str(q)[:200] for q in data.get("suggested_questions", [])[:3]]
        return one_liner, bullets, questions

    except Exception as e:
        logger.warning("Document analysis failed", filename=filename, error=str(e))
        return "", [], []
