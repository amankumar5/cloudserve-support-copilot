from app.evaluation.evaluator import evaluator


def test_evaluator_metrics():
    ret = evaluator.evaluate_retrieval(
        retrieved_file_names=["doc1.pdf", "doc2.pdf"],
        expected_file_names=["doc1.pdf"],
        retrieved_page_numbers=[1, 2],
        expected_page_numbers=[1],
        k=5
    )

    assert ret["recall_at_k"] == 1.0
    assert ret["mrr"] == 1.0

    ans_eval = evaluator.evaluate_answer_faithfulness(
        question="What is the remote work policy?",
        answer="The retrieved documents do not contain enough information to answer this question.",
        expected_answer=None,
        is_unanswerable=True
    )
    assert ans_eval["unanswerable_detection"] == 1.0
