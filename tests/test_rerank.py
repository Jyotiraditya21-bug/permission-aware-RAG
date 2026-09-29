import pytest
from src.models import RetrievalResult, Version
from src.retrieval.rerank import RerankingPipeline

class MockReranker:
    def __init__(self, scores):
        self.scores = scores
    
    async def rerank(self, query, texts):
        if isinstance(self.scores, Exception):
            raise self.scores
        return self.scores

def make_result(chunk_id, rank):
    return RetrievalResult(
        chunk_id=chunk_id,
        text=f"text {chunk_id}",
        version=Version(document_version="v1", corpus_version="v1", acl_version="a1"),
        fusion_rank=rank,
    )

@pytest.mark.asyncio
async def test_rerank_candidates():
    cands = [make_result("c1", 1), make_result("c2", 2), make_result("c3", 3)]
    
    # Reranker favors c3 > c1 > c2
    reranker = MockReranker((0.5, 0.2, 0.9))
    pipeline = RerankingPipeline(reranker, evidence_budget=2)
    
    results = await pipeline.rerank_candidates("query", cands)
    
    assert len(results) == 2
    assert results[0].chunk_id == "c3"
    assert results[0].rerank_score == 0.9
    assert results[1].chunk_id == "c1"
    assert results[1].rerank_score == 0.5

@pytest.mark.asyncio
async def test_rerank_fallback_on_failure():
    cands = [make_result("c1", 1), make_result("c2", 2)]
    
    reranker = MockReranker(RuntimeError("Model offline"))
    pipeline = RerankingPipeline(reranker, evidence_budget=5)
    
    results = await pipeline.rerank_candidates("query", cands)
    
    assert len(results) == 2
    assert results[0].chunk_id == "c1"
    assert results[1].chunk_id == "c2"
    assert results[0].rerank_score == 0.0
    
@pytest.mark.asyncio
async def test_rerank_empty():
    reranker = MockReranker((0.9,))
    pipeline = RerankingPipeline(reranker)
    assert await pipeline.rerank_candidates("query", []) == ()
