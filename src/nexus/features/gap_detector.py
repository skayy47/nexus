"""Knowledge Gap Detective — flags missing information in the corpus."""

from __future__ import annotations

import json

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class GapReport(BaseModel):
    """A detected knowledge gap in the corpus."""

    topic: str
    description: str
    what_doc_would_help: str = ""
    severity: str = "medium"


_GAP_PROMPT = """\
You are a knowledge gap detector for a document intelligence system.

A user asked: "{question}"

The system retrieved documents but the confidence score was only {confidence:.0%}.

Corpus documents available: {doc_names}

Determine if this is a genuine KNOWLEDGE GAP — meaning the corpus is missing \
documentation that should exist for a functioning organization.

Respond in JSON:
{{
  "is_gap": true or false,
  "topic": "short name for the missing topic (5 words max)",
  "description": "one sentence describing what knowledge is missing",
  "what_doc_would_help": "what type of document would fill this gap (e.g. 'HR policy on remote work')"
}}

Only flag as a gap if this is something an organization's knowledge base SHOULD have documented.
If the question is off-topic or unrelated to business operations, return {{"is_gap": false}}.
"""


_FR_JSON_DIRECTIVE = (
    "\n\nWrite every natural-language value (topic, description, "
    "what_doc_would_help) in French. Keep the JSON keys exactly as specified."
)


async def detect_gaps(
    query: str,
    confidence_score: float,
    doc_names: list[str],
    language: str = "en",
) -> GapReport | None:
    """Detect knowledge gap when retrieval confidence is low.

    Only fires when confidence_score < 0.45 and at least one document exists.
    Returns GapReport if gap detected, None otherwise.
    """
    if confidence_score >= 0.45 or not doc_names:
        return None

    from nexus.rag.llm_client import single_call

    prompt = _GAP_PROMPT.format(
        question=query,
        confidence=confidence_score,
        doc_names=", ".join(doc_names[:10]),
    )
    if (language or "en").strip().lower().startswith("fr"):
        prompt = prompt + _FR_JSON_DIRECTIVE

    try:
        raw = await single_call(prompt, max_tokens=200, temperature=0.0)
        raw = raw.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data = json.loads(raw)
        if not data.get("is_gap"):
            return None

        return GapReport(
            topic=data.get("topic", "Unknown topic")[:60],
            description=data.get("description", "")[:200],
            what_doc_would_help=data.get("what_doc_would_help", "")[:150],
        )

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Gap detection parse failed", error=str(e))
        return None
    except Exception as e:
        logger.error("Gap detection failed", error=str(e))
        return None
