"""End-to-end integration tests for the NEXUS API.

Uses synchronous httpx.Client — no async/event-loop complexity.
SSE streaming is handled via httpx's sync streaming context.

Assumptions:
- Backend is running on http://localhost:8000 (or NEXUS_API_URL env var).
- Tests auto-skip if the backend is unreachable.
- Tests run in declaration order — the delete test is last.

Run:
    cd nexus
    PYTHONPATH=src py -3.11 -m pytest tests/integration/test_e2e.py -v -m integration

Skip in CI (no backend):
    py -3.11 -m pytest -m "not integration"
"""

from __future__ import annotations

import json
import os
from collections.abc import Generator

import httpx
import pytest

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("NEXUS_API_URL", "http://localhost:8000")
TIMEOUT  = httpx.Timeout(90.0)   # demo load + embedding warmup can be slow

DEMO_DOC_NAMES = {
    "TechCorp_HR_Policy_2023.txt",
    "TechCorp_HR_Policy_2024.txt",
    "Q3_2023_Financial_Summary.txt",
    "Q4_2023_Financial_Summary.txt",
    "Product_Roadmap_2024.txt",
}

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _backend_reachable() -> bool:
    try:
        with httpx.Client(timeout=2.0) as c:
            return c.get(f"{BASE_URL}/health").status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def _collect_sse(
    client: httpx.Client,
    question: str,
    session_id: str = "e2e-session",
) -> list[dict]:
    """POST /chat and collect all SSE events synchronously."""
    events: list[dict] = []
    with client.stream(
        "POST",
        "/chat",
        json={"question": question, "session_id": session_id, "transparency_mode": True},
    ) as resp:
        assert resp.status_code == 200, f"/chat returned {resp.status_code}"
        buf = ""
        for chunk in resp.iter_text():
            buf += chunk
            while "\n\n" in buf:
                block, buf = buf.split("\n\n", 1)
                etype = edata = None
                for line in block.splitlines():
                    if line.startswith("event: "):
                        etype = line[7:]
                    elif line.startswith("data: "):
                        try:
                            edata = json.loads(line[6:])
                        except json.JSONDecodeError:
                            edata = {}
                if etype and edata is not None:
                    events.append({"type": etype, "data": edata})
    return events


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client() -> Generator[httpx.Client, None, None]:
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module", autouse=True)
def load_demo(client: httpx.Client) -> None:
    """Load the demo corpus once before all tests in this module."""
    if not _backend_reachable():
        pytest.skip("Backend not reachable — skipping all integration tests")

    r = client.post("/demo")
    assert r.status_code == 200, f"POST /demo failed: {r.text}"
    body = r.json()
    assert body["documents_loaded"] == 5, (
        f"Expected 5 demo docs loaded, got {body['documents_loaded']}"
    )


# ---------------------------------------------------------------------------
# Test 1 — Health
# ---------------------------------------------------------------------------


def test_health(client: httpx.Client) -> None:
    """GET /health returns status=ok with chunks > 0 after demo load."""
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["indexed_chunks"] > 0, "Expected indexed_chunks > 0 after demo load"


# ---------------------------------------------------------------------------
# Test 2 — GET /documents lists all 5 demo files
# ---------------------------------------------------------------------------


def test_get_documents_lists_all_demo_docs(client: httpx.Client) -> None:
    """GET /documents returns all 5 demo filenames, each with chunk_count > 0."""
    r = client.get("/documents")
    assert r.status_code == 200

    body = r.json()
    assert "documents" in body

    returned = {d["name"] for d in body["documents"]}
    assert returned == DEMO_DOC_NAMES, (
        f"Document names mismatch.\nExpected: {DEMO_DOC_NAMES}\nGot:      {returned}"
    )
    for doc in body["documents"]:
        assert doc["chunk_count"] > 0, (
            f"Document '{doc['name']}' has chunk_count={doc['chunk_count']}"
        )


# ---------------------------------------------------------------------------
# Test 3 — Chat streams tokens + transparency event with HR sources
# ---------------------------------------------------------------------------


def test_chat_tokens_and_transparency(client: httpx.Client) -> None:
    """POST /chat streams token events + transparency event citing HR docs."""
    events = _collect_sse(client, "What is the remote work policy?", "e2e-hr-1")
    types  = [e["type"] for e in events]

    assert any(e["type"] == "token" for e in events), (
        "Expected at least one 'token' event"
    )
    assert "transparency" in types, (
        f"Expected a 'transparency' event. Got: {types}"
    )
    assert "done" in types, "Stream must end with a 'done' event"

    transparency = next(e["data"] for e in events if e["type"] == "transparency")

    score = transparency.get("confidence_score") or transparency.get("score", -1)
    assert 0.0 <= score <= 1.0, f"confidence_score out of range: {score}"

    sources = transparency.get("sources", [])
    assert sources, "Transparency event must include at least one source"

    source_docs = {s["document_name"] for s in sources}
    hr_docs = {"TechCorp_HR_Policy_2023.txt", "TechCorp_HR_Policy_2024.txt"}
    assert source_docs & hr_docs, (
        f"Expected HR policy files in sources, got: {source_docs}"
    )


# ---------------------------------------------------------------------------
# Test 4 — Contradiction event fires for known HR policy conflict
# ---------------------------------------------------------------------------


def test_chat_triggers_contradiction(client: httpx.Client) -> None:
    """Remote work policy query surfaces the 2023 (3 days) vs 2024 (2 days) conflict."""
    events = _collect_sse(client, "what is the remote work policy", "e2e-contradiction-1")
    types  = [e["type"] for e in events]

    assert "contradiction" in types, (
        f"Expected a 'contradiction' event.\nGot: {types}\n"
        "HR 2023 (3 days/week) vs HR 2024 (2 days/week) should conflict."
    )

    c = next(e["data"] for e in events if e["type"] == "contradiction")
    for field in ("excerpt_a", "excerpt_b", "source_a", "source_b", "explanation"):
        assert c.get(field), f"contradiction.{field} must be non-empty"

    hr_docs = {"TechCorp_HR_Policy_2023.txt", "TechCorp_HR_Policy_2024.txt"}
    assert {c["source_a"], c["source_b"]} & hr_docs, (
        f"Contradiction should involve HR policy files. Got: {c['source_a']}, {c['source_b']}"
    )


# ---------------------------------------------------------------------------
# Test 5 — Insights reports correct document count
# ---------------------------------------------------------------------------


def test_insights_document_count(client: httpx.Client) -> None:
    """GET /insights returns document_count == 5 after demo load."""
    r = client.get("/insights")
    assert r.status_code == 200
    body = r.json()
    assert body["document_count"] == 5, (
        f"Expected document_count=5, got {body['document_count']}"
    )


# ---------------------------------------------------------------------------
# Test 6 — DELETE /documents resets to zero  (must be last)
# ---------------------------------------------------------------------------


def test_delete_documents_resets_to_zero(client: httpx.Client) -> None:
    """DELETE /documents clears all chunks; subsequent endpoints confirm empty state."""
    r = client.delete("/documents")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    r = client.get("/documents")
    assert r.status_code == 200
    assert r.json()["documents"] == [], (
        f"Expected empty list after DELETE, got: {r.json()['documents']}"
    )

    r = client.get("/insights")
    assert r.status_code == 200
    assert r.json()["document_count"] == 0, (
        f"Expected document_count=0 after DELETE, got: {r.json()['document_count']}"
    )
