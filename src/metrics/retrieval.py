"""Retrieval metrics reporting recall@k and MRR without leaking content."""
from typing import Sequence
from src.models import Contract, Route

class RetrievalMetric(Contract):
    trace_id: str
    route: Route
    is_cached: bool
    candidate_count: int
    k_measured: int | None
    recall_at_k: float | None
    mrr: float | None
    applicable: bool

def calculate_retrieval_metrics(
    trace_id: str,
    route: Route,
    retrieved_chunk_ids: Sequence[str],
    labeled_relevant_chunk_ids: set[str] | None,
    is_cached: bool = False,
) -> RetrievalMetric:
    """Calculate retrieval metrics for a query trace."""
    if route == "no-retrieval-needed":
        return RetrievalMetric(
            trace_id=trace_id,
            route=route,
            is_cached=is_cached,
            candidate_count=0,
            k_measured=None,
            recall_at_k=None,
            mrr=None,
            applicable=False,
        )

    if labeled_relevant_chunk_ids is None or not labeled_relevant_chunk_ids:
        # Zero permitted relevance or missing labels
        return RetrievalMetric(
            trace_id=trace_id,
            route=route,
            is_cached=is_cached,
            candidate_count=len(retrieved_chunk_ids),
            k_measured=len(retrieved_chunk_ids),
            recall_at_k=None,
            mrr=None,
            applicable=True if labeled_relevant_chunk_ids is None else False,
        )

    k = len(retrieved_chunk_ids)
    hits = sum(1 for cid in retrieved_chunk_ids if cid in labeled_relevant_chunk_ids)
    recall = hits / len(labeled_relevant_chunk_ids)
    
    mrr = 0.0
    for rank, cid in enumerate(retrieved_chunk_ids, start=1):
        if cid in labeled_relevant_chunk_ids:
            mrr = 1.0 / rank
            break

    return RetrievalMetric(
        trace_id=trace_id,
        route=route,
        is_cached=is_cached,
        candidate_count=k,
        k_measured=k,
        recall_at_k=recall,
        mrr=mrr,
        applicable=True,
    )
