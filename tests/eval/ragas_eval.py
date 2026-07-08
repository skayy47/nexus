"""RAGAS evaluation script — run after demo data is loaded.

Usage:
    py -3.11 tests/eval/ragas_eval.py

Requires:
    - Demo loaded in Supabase (POST /demo or equivalent)
    - .env with GROQ_API_KEY set

Notes:
    - Answer generation uses settings.groq_model — the exact model production
      serves — so scores are honest and representative of what real users get.
      Previously this hardcoded llama-3.1-8b-instant to save quota, which meant
      the published scores never measured the real (70B) production model.
    - A full 20-question run on the 70B model costs roughly 65-70K tokens
      against Groq's 100K token-per-day free-tier limit for that model — tight
      if anything else exercised the 70B model recently. This is a rolling
      window, not a calendar-day reset: Groq's own error message states the
      exact wait (e.g. "try again in 26m4s"), which this script now surfaces.
      Rows are written to rows_cache.json after every successful row (not just
      at the end), so a mid-run quota exhaustion preserves progress — re-run
      this script after the stated wait to resume, not restart. Do not revert
      to a smaller model to dodge this constraint.
    - Delete rows_cache.json to force full regeneration.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

# Force Groq for local eval — langchain-google-genai is not installed locally.
# pydantic-settings gives env vars priority over .env file, so this overrides
# LLM_BACKEND=gemini in .env before get_settings() is first called.
os.environ["LLM_BACKEND"] = "groq"

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"
RESULTS_PATH = Path(__file__).parent / "results.json"
ROWS_CACHE_PATH = Path(__file__).parent / "rows_cache.json"


async def run_single(question: str, ground_truth: str) -> dict:
    """Run a single QA pair through the RAG pipeline."""
    from nexus.index.hybrid_retriever import hybrid_retrieve
    from nexus.rag.chain import format_context, build_messages
    from nexus.rag.embeddings import embed_query
    from nexus.config import get_settings
    from langchain_groq import ChatGroq

    settings = get_settings()
    query_vec = embed_query(question)
    chunks = await hybrid_retrieve(question, query_vec, k=settings.retrieval_k)
    contexts = [c.content for c in chunks]

    # Use the real production model so scores reflect what users actually get.
    llm = ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0.1, max_tokens=512)
    context_str = format_context(chunks)
    messages = build_messages(question, context_str)
    from langchain_core.messages import SystemMessage, HumanMessage
    lc_msgs = [
        (SystemMessage if m["role"] == "system" else HumanMessage)(content=m["content"])
        for m in messages
    ]
    response = await llm.ainvoke(lc_msgs)
    answer = str(response.content)

    return {
        "user_input": question,
        "response": answer,
        "retrieved_contexts": contexts,
        "reference": ground_truth,
    }


async def generate_rows(test_cases: list[dict]) -> list[dict]:
    """Generate answers for all test cases, resuming from a partial cache if present.

    Rows are written to disk after every successful question, so a mid-run
    quota exhaustion (Groq 429) preserves progress — re-running this script
    picks up only the remaining questions instead of starting over.
    """
    rows: list[dict] = []
    done_questions: set[str] = set()
    if ROWS_CACHE_PATH.exists():
        rows = json.loads(ROWS_CACHE_PATH.read_text())
        done_questions = {r["user_input"] for r in rows}
        if done_questions:
            print(f"  (resuming — {len(done_questions)}/{len(test_cases)} rows already cached)")

    for i, tc in enumerate(test_cases, 1):
        if tc["question"] in done_questions:
            continue
        print(f"  [{i}/{len(test_cases)}] {tc['question'][:60]}...")
        try:
            row = await run_single(tc["question"], tc["ground_truth"])
            rows.append(row)
            ROWS_CACHE_PATH.write_text(json.dumps(rows, indent=2))
        except Exception as e:
            msg = str(e)
            if "429" in msg or "rate_limit" in msg.lower() or "rate limit" in msg.lower():
                # Groq's TPD limit is a rolling window, not a calendar-day reset —
                # the error message includes the real wait time, e.g. "try again
                # in 26m4.704s". Surface it instead of assuming "tomorrow".
                wait_match = re.search(r"try again in ([\d.]+m[\d.]+s|[\d.]+s)", msg)
                wait_str = f" — retry in {wait_match.group(1)}" if wait_match else " — re-run once quota resets"
                print(f"  QUOTA EXHAUSTED after {len(rows)}/{len(test_cases)} rows{wait_str}.")
                print("  Progress saved to rows_cache.json — re-running this script will resume, not restart.")
                return rows
            print(f"  ERROR: {e}")

    return rows


async def main() -> None:
    test_cases = json.loads(TEST_CASES_PATH.read_text())
    print(f"Running RAGAS evaluation on {len(test_cases)} test cases...")

    # The BM25 index is an in-memory singleton built by the API process when
    # /demo is called — it does NOT persist across separate process runs.
    # Running this script fresh (as its own process) previously meant BM25
    # was silently empty for the entire eval (sparse_hits=0 every query),
    # meaning "hybrid" retrieval was actually dense-only. Build it here so
    # this script's process has real sparse search too.
    from nexus.index.bm25_index import get_bm25_index
    from nexus.index.supabase_store import get_all_chunks

    all_chunks = await get_all_chunks()
    if not all_chunks:
        print("No chunks found in Supabase — load the demo corpus first (POST /demo).")
        return
    get_bm25_index().build(all_chunks)
    print(f"  BM25 index built from {len(all_chunks)} chunks.")

    rows = await generate_rows(test_cases)

    if not rows:
        print("No rows collected — aborting.")
        return

    if len(rows) < len(test_cases):
        print(
            f"\nOnly {len(rows)}/{len(test_cases)} rows collected (quota exhausted mid-run). "
            "Not scoring a partial set — re-run this script to finish the remaining "
            "questions before publishing results."
        )
        return

    # ragas 0.2 API
    import math

    from ragas import EvaluationDataset, evaluate
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import AnswerRelevancy, ContextRecall, Faithfulness

    from langchain_community.embeddings import HuggingFaceEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from nexus.config import get_settings

    settings = get_settings()
    # Use Qwen3-32b — separate quota bucket, strong reasoning model.
    # Disable thinking mode so RAGAS can parse clean JSON responses.
    from langchain_groq import ChatGroq
    ragas_llm = LangchainLLMWrapper(
        ChatGroq(
            model="qwen/qwen3-32b",
            api_key=settings.groq_api_key,
            temperature=0.0,
            max_tokens=1024,
            model_kwargs={"reasoning_effort": "none"},
        )
    )
    embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    )

    from ragas.run_config import RunConfig

    dataset = EvaluationDataset.from_list(rows)
    result = evaluate(
        dataset=dataset,
        metrics=[Faithfulness(llm=ragas_llm), AnswerRelevancy(llm=ragas_llm), ContextRecall(llm=ragas_llm)],
        embeddings=embeddings,
        raise_exceptions=False,
        run_config=RunConfig(timeout=120, max_retries=2, max_wait=30, max_workers=1),
    )

    def safe_mean(values) -> float:
        valid = [v for v in values if v is not None and isinstance(v, (int, float)) and not math.isnan(v)]
        return round(sum(valid) / len(valid), 4) if valid else 0.0

    def extract(key: str) -> float:
        val = result[key]
        if isinstance(val, list):
            return safe_mean(val)
        return round(float(val), 4)

    scores = {
        "faithfulness": extract("faithfulness"),
        "answer_relevancy": extract("answer_relevancy"),
        "context_recall": extract("context_recall"),
    }

    RESULTS_PATH.write_text(json.dumps(scores, indent=2))

    print("\nRAGAS EVALUATION COMPLETE")
    print(json.dumps(scores, indent=2))

    targets = {"faithfulness": 0.85, "answer_relevancy": 0.80, "context_recall": 0.75}
    all_pass = True
    for metric, target in targets.items():
        status = "PASS" if scores[metric] >= target else "FAIL"
        if scores[metric] < target:
            all_pass = False
        print(f"  {metric}: {scores[metric]} (target {target}) — {status}")

    if not all_pass:
        print("\nSome scores below target. Consider: increase k, tune chunk size.")
    else:
        print("\nAll targets met. Ready to ship.")


if __name__ == "__main__":
    asyncio.run(main())
