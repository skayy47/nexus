"""RAGAS evaluation script — run after demo data is loaded.

Usage:
    py -3.11 tests/eval/ragas_eval.py

Requires:
    - Demo loaded in Supabase (POST /demo or equivalent)
    - .env with GROQ_API_KEY set

Notes:
    - Answer generation uses llama-3.1-8b-instant (lower TPD cost) so the
      100K/day limit is not exhausted before RAGAS scoring begins.
    - Production answers use llama-3.3-70b-versatile; eval uses 8b to stay
      within free-tier daily limits.
    - Rows are cached to rows_cache.json — delete it to re-generate answers.
"""

from __future__ import annotations

import asyncio
import json
import os
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

# Use 8b-instant for eval answer generation — same retrieval quality test,
# but uses 6M TPD instead of 100K so scoring doesn't hit the daily limit.
EVAL_ANSWER_MODEL = "llama-3.1-8b-instant"


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

    # Use 8b-instant for eval generation (won't exhaust daily TPD limit)
    llm = ChatGroq(model=EVAL_ANSWER_MODEL, api_key=settings.groq_api_key, temperature=0.1, max_tokens=512)
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
    """Generate answers for all test cases, using cache if available."""
    if ROWS_CACHE_PATH.exists():
        print("  (using cached rows — delete rows_cache.json to regenerate)")
        return json.loads(ROWS_CACHE_PATH.read_text())

    rows = []
    for i, tc in enumerate(test_cases, 1):
        print(f"  [{i}/{len(test_cases)}] {tc['question'][:60]}...")
        try:
            row = await run_single(tc["question"], tc["ground_truth"])
            rows.append(row)
        except Exception as e:
            print(f"  ERROR: {e}")

    ROWS_CACHE_PATH.write_text(json.dumps(rows, indent=2))
    return rows


async def main() -> None:
    test_cases = json.loads(TEST_CASES_PATH.read_text())
    print(f"Running RAGAS evaluation on {len(test_cases)} test cases...")

    rows = await generate_rows(test_cases)

    if not rows:
        print("No rows collected — aborting.")
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
        run_config=RunConfig(timeout=120, max_retries=3, max_wait=60, max_workers=4),
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
