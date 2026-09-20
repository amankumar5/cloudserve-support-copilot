import json
import os
from typing import List, Dict, Any
from app.models.api import QueryRequest
from app.api.routes import query_documents
from app.evaluation.evaluator import evaluator
from app.core.config import settings
from app.core.logging import logger


class BenchmarkRunner:
    """
    Runner executing evaluation benchmarks against test dataset.
    """

    def __init__(self, dataset_path: str = "data/evaluation_dataset.json"):
        self.dataset_path = dataset_path

    def load_dataset(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.dataset_path):
            logger.warning(f"Dataset path {self.dataset_path} not found.")
            return []
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_evaluations(self) -> Dict[str, Any]:
        items = self.load_dataset()
        if not items:
            return {"status": "no_data", "summary": {}}

        total = len(items)
        recalls = []
        precisions = []
        mrrs = []
        faithfulness_scores = []

        results_detail = []

        for item in items:
            q = item["question"]
            req = QueryRequest(question=q, top_k=5)
            response = query_documents(req)

            retrieved_files = [s.document_name for s in response.sources]
            retrieved_pages = [s.page_number for s in response.sources]

            exp_files = [s["file_name"] for s in item.get("expected_sources", [])]
            exp_pages = [s["page_number"] for s in item.get("expected_sources", [])]

            ret_eval = evaluator.evaluate_retrieval(
                retrieved_file_names=retrieved_files,
                expected_file_names=exp_files,
                retrieved_page_numbers=retrieved_pages,
                expected_page_numbers=exp_pages,
                k=5
            )

            ans_eval = evaluator.evaluate_answer_faithfulness(
                question=q,
                answer=response.answer,
                expected_answer=item.get("expected_answer"),
                is_unanswerable=item.get("is_unanswerable", False)
            )

            recalls.append(ret_eval["recall_at_k"])
            precisions.append(ret_eval["precision_at_k"])
            mrrs.append(ret_eval["mrr"])
            faithfulness_scores.append(ans_eval["faithfulness"])

            results_detail.append({
                "id": item["id"],
                "question": q,
                "category": item.get("category", "text"),
                "answer": response.answer,
                "sources_count": len(response.sources),
                "recall_at_5": ret_eval["recall_at_k"],
                "mrr": ret_eval["mrr"],
                "faithfulness": ans_eval["faithfulness"]
            })

        avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
        avg_precision = sum(precisions) / len(precisions) if precisions else 0.0
        avg_mrr = sum(mrrs) / len(mrrs) if mrrs else 0.0
        avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else 0.0

        summary = {
            "total_questions": total,
            "mean_recall_at_5": round(avg_recall, 4),
            "mean_precision_at_5": round(avg_precision, 4),
            "mrr": round(avg_mrr, 4),
            "mean_faithfulness": round(avg_faithfulness, 4)
        }

        return {
            "summary": summary,
            "details": results_detail
        }


benchmark_runner = BenchmarkRunner()
