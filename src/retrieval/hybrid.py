"""Hybrid retrieval combining lexical and dense search via reciprocal rank fusion."""
from src.indexes.base import IndexBackend
from src.ingestion.pipeline import Embedder
from src.models import AccessScope, Chunk, RetrievalResult, Version
from src.retrieval.fusion import reciprocal_rank_fusion


class HybridRetriever:
    def __init__(
        self,
        lexical_index: IndexBackend,
        dense_index: IndexBackend,
        embedder: Embedder,
        top_k: int = 10,
    ) -> None:
        self.lexical = lexical_index
        self.dense = dense_index
        self.embedder = embedder
        self.top_k = top_k

    async def search(
        self,
        queries: tuple[str, ...],
        scope: AccessScope,
        corpus_version: str,
    ) -> tuple[RetrievalResult, ...]:
        """Execute hybrid search across multiple subqueries for a unified access scope."""
        if not queries:
            return ()

        # Ensure all subqueries use same scope and version
        all_lexical_cands: list[tuple[tuple[str, float], ...]] = []
        all_dense_cands: list[tuple[tuple[str, float], ...]] = []
        
        # Store chunks to construct RetrievalResult later
        chunk_map: dict[str, Chunk] = {}
        lexical_scores: dict[str, float] = {}
        dense_scores: dict[str, float] = {}

        # Embed all subqueries
        vectors = await self.embedder.embed(queries)
        if not vectors or len(vectors) != len(queries):
            raise RuntimeError("Embedder failed to produce vectors for all subqueries")

        for query_text, query_vector in zip(queries, vectors, strict=True):
            # Run both searches pre-filtered by ACL
            lex_results = self.lexical.search(
                scope=scope, corpus_version=corpus_version, top_k=self.top_k, query_text=query_text
            )
            den_results = self.dense.search(
                scope=scope, corpus_version=corpus_version, top_k=self.top_k, query_vector=query_vector
            )
            
            lex_cands = []
            for chunk, score in lex_results:
                chunk_map[chunk.chunk_id] = chunk
                lexical_scores[chunk.chunk_id] = max(lexical_scores.get(chunk.chunk_id, score), score)
                lex_cands.append((chunk.chunk_id, score))
                
            den_cands = []
            for chunk, score in den_results:
                chunk_map[chunk.chunk_id] = chunk
                dense_scores[chunk.chunk_id] = max(dense_scores.get(chunk.chunk_id, score), score)
                den_cands.append((chunk.chunk_id, score))
                
            all_lexical_cands.append(tuple(lex_cands))
            all_dense_cands.append(tuple(den_cands))

        # RRF across all subqueries and both index types
        fused = reciprocal_rank_fusion(*(all_lexical_cands + all_dense_cands))
        
        results = []
        for chunk_id, (rank, _) in fused.items():
            chunk = chunk_map[chunk_id]
            results.append(RetrievalResult(
                chunk_id=chunk_id,
                text=chunk.text,
                version=Version(
                    document_version=chunk.document_version,
                    corpus_version=corpus_version,
                    acl_version=chunk.acl.acl_version,
                ),
                lexical_score=lexical_scores.get(chunk_id),
                dense_score=dense_scores.get(chunk_id),
                fusion_rank=rank,
            ))
            
        results.sort(key=lambda r: r.fusion_rank)
        return tuple(results)
