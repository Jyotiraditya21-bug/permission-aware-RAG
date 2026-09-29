from src.metrics.retrieval import calculate_retrieval_metrics

def test_calculate_metrics():
    # Hits at rank 2
    m = calculate_retrieval_metrics(
        trace_id="t1",
        route="direct-retrieve",
        retrieved_chunk_ids=["c1", "c2", "c3"],
        labeled_relevant_chunk_ids={"c2", "c4"}
    )
    assert m.candidate_count == 3
    assert m.recall_at_k == 0.5
    assert m.mrr == 0.5
    assert m.applicable is True

def test_no_retrieval_needed():
    m = calculate_retrieval_metrics(
        trace_id="t1",
        route="no-retrieval-needed",
        retrieved_chunk_ids=[],
        labeled_relevant_chunk_ids={"c1"}
    )
    assert m.applicable is False

def test_zero_relevance():
    m = calculate_retrieval_metrics(
        trace_id="t1",
        route="direct-retrieve",
        retrieved_chunk_ids=["c1"],
        labeled_relevant_chunk_ids=set()
    )
    assert m.applicable is False
    assert m.recall_at_k is None
