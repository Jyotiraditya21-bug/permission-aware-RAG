"""Reranking and bounding candidate evidence sets."""
from typing import Protocol, Sequence
from src.models import RetrievalResult

class Reranker(Protocol):
    async def rerank(self, query: str, texts: Sequence[str]) -> tuple[float, ...]:
        ...

class RerankingPipeline:
    def __init__(self, reranker: Reranker, evidence_budget: int = 5) -> None:
        self.reranker = reranker
        self.evidence_budget = evidence_budget

    async def rerank_candidates(
        self, query: str, candidates: Sequence[RetrievalResult]
    ) -> tuple[RetrievalResult, ...]:
        """Rerank candidates against the original query and enforce budget."""
        if not candidates:
            return ()
            
        texts = [c.text for c in candidates]
        
        try:
            scores = await self.reranker.rerank(query, texts)
            if len(scores) != len(candidates):
                raise RuntimeError("Reranker returned mismatched scores count")
        except Exception:
            # Fallback to fusion rank (preserve original order)
            scores = tuple(0.0 for _ in candidates)
            
        scored = []
        for cand, score in zip(candidates, scores, strict=True):
            cand_copy = cand.model_copy(update={"rerank_score": score})
            scored.append(cand_copy)
            
        # Sort by rerank score descending, then fallback to original fusion_rank
        scored.sort(key=lambda c: (c.rerank_score or 0.0, -c.fusion_rank), reverse=True)
        return tuple(scored[:self.evidence_budget])
