from app.retrieval.query_processor import query_processor


def test_query_intent_classification():
    t_intent = query_processor.classify_intent("Which product had the highest revenue?")
    assert t_intent == "table_query"

    d_intent = query_processor.classify_intent("Explain the payment architecture diagram and components")
    assert d_intent == "diagram_query"

    l_intent = query_processor.classify_intent("What is error code 504?")
    assert l_intent in ["exact_lookup", "text_query"]
