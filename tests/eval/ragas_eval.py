"""RAGAS evaluation script — run after demo data is loaded.

Usage:
    py -3.11 tests/eval/ragas_eval.py

Requires:
    - Backend running: uvicorn nexus.api.main:app
    - Demo loaded: POST /demo
    - .env with GROQ_API_KEY set
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"
RESULTS_PATH = Path(__file__).parent / "results.json"


async def run_single(question: str, ground_truth: str) -> dict:
    """Run a single QA pair through the RAG pipeline."""
    from nexus.index.hybrid_retriever import hybrid_retrieve
    from nexus.rag.chain import generate_answer_full
    from nexus.rag.embeddings import embed_query

    query_vec = embed_query(question)
    chunks = await hybrid_retrieve(question, query_vec, k=6)
    contexts = [c.content for c in chunks]
    answer = await generate_answer_full(question, chunks)

    return {
        "user_input": question,
        "response": answer,
        "retrieved_contexts": contexts,
        "reference": ground_truth,
    }


async def main() -> None:
    test_cases = json.loads(TEST_CASES_PATH.read_text())
    print(f"Running RAGAS evaluation on {len(test_cases)} test cases...")

    rows = []
    for i, tc in enumerate(test_cases, 1):
        print(f"  [{i}/{len(test_cases)}] {tc['question'][:60]}...")
        try:
            row = await run_single(tc["question"], tc["ground_truth"])
            rows.append(row)
        except Exception as e:
            print(f"  ERROR: {e}")

    if not rows:
        print("No rows collected — aborting.")
        return

    # ragas 0.2 API
    from ragas import EvaluationDataset, evaluate
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import AnswerRelevancy, ContextRecall, Faithfulness

    from langchain_groq import ChatGroq
    from nexus.config import get_settings

    settings = get_settings()
    llm = LangchainLLMWrapper(ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key))

    dataset = EvaluationDataset.from_list(rows)
    result = evaluate(
        dataset=dataset,
        metrics=[Faithfulness(llm=llm), AnswerRelevancy(llm=llm), ContextRecall(llm=llm)],
    )

    scores = {
        "faithfulness": round(float(result["faithfulness"]), 4),
        "answer_relevancy": round(float(result["answer_relevancy"]), 4),
        "context_recall": round(float(result["context_recall"]), 4),
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
