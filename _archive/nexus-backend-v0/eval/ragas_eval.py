"""RAGAS evaluation script — run after Week 2 demo data is loaded."""
import asyncio
import json
from pathlib import Path

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall

from core.retrieval import hybrid_retrieve
from core.llm import stream_answer

TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"
RESULTS_PATH = Path(__file__).parent / "results.json"


async def run_single(question: str, ground_truth: str) -> dict:
    chunks = await hybrid_retrieve(question, k=6)
    contexts = [c.content for c in chunks]

    tokens = []
    async for token in stream_answer(question, chunks):
        tokens.append(token)
    answer = "".join(tokens)

    return {
        "question": question,
        "answer": answer,
        "contexts": contexts,
        "ground_truth": ground_truth,
    }


async def main():
    test_cases = json.loads(TEST_CASES_PATH.read_text())
    print(f"Running RAGAS evaluation on {len(test_cases)} test cases...")

    rows = []
    for i, tc in enumerate(test_cases, 1):
        print(f"  [{i}/{len(test_cases)}] {tc['question'][:60]}...")
        row = await run_single(tc["question"], tc["ground_truth"])
        rows.append(row)

    dataset = Dataset.from_list(rows)
    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_recall])

    scores = {
        "faithfulness": round(float(result["faithfulness"]), 4),
        "answer_relevancy": round(float(result["answer_relevancy"]), 4),
        "context_recall": round(float(result["context_recall"]), 4),
    }

    RESULTS_PATH.write_text(json.dumps(scores, indent=2))
    print("\nRATINGS EVALUATION COMPLETE")
    print(json.dumps(scores, indent=2))

    targets = {"faithfulness": 0.85, "answer_relevancy": 0.80, "context_recall": 0.75}
    for metric, target in targets.items():
        status = "PASS" if scores[metric] >= target else "FAIL"
        print(f"  {metric}: {scores[metric]} (target {target}) — {status}")


if __name__ == "__main__":
    asyncio.run(main())
