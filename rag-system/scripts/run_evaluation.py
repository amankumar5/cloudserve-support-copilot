import sys
import os
import json

# Ensure parent path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.evaluation.benchmark import benchmark_runner


def main():
    print("=" * 60)
    print("Running Multimodal RAG Benchmark & Evaluation Suite")
    print("=" * 60)

    res = benchmark_runner.run_evaluations()
    summary = res.get("summary", {})

    print("\n--- SUMMARY METRICS ---")
    print(f"Total Test Cases:    {summary.get('total_questions', 0)}")
    print(f"Recall@5:            {summary.get('mean_recall_at_5', 0.0):.4f}")
    print(f"Precision@5:         {summary.get('mean_precision_at_5', 0.0):.4f}")
    print(f"MRR (Mean Recip. Rank): {summary.get('mrr', 0.0):.4f}")
    print(f"Faithfulness Score:  {summary.get('mean_faithfulness', 0.0):.4f}")
    print("=" * 60)

    print("\n--- DETAILED TEST BREAKDOWN ---")
    for d in res.get("details", []):
        print(f"\nID: {d['id']} [{d['category'].upper()}]")
        print(f"Question:     {d['question']}")
        print(f"Recall@5:     {d['recall_at_5']} | MRR: {d['mrr']} | Faithfulness: {d['faithfulness']}")
        print(f"Answer Snippet: {d['answer'][:150]}...")


if __name__ == "__main__":
    main()
