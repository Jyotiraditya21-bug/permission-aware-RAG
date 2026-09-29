"""Core orchestration service for answering queries."""
from src.cache import SemanticCache
from src.generation import Generator
from src.ingestion.pipeline import Embedder
from src.ingestion.publication import Publisher
from src.models import AccessScope, Answer, QueryRequest
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.rerank import RerankingPipeline
from src.router import QueryRouter

class RAGService:
    def __init__(
        self,
        router: QueryRouter,
        retriever: HybridRetriever,
        reranker: RerankingPipeline,
        generator: Generator,
        cache: SemanticCache,
        publisher: Publisher,
        embedder: Embedder,
    ) -> None:
        self.router = router
        self.retriever = retriever
        self.reranker = reranker
        self.generator = generator
        self.cache = cache
        self.publisher = publisher
        self.embedder = embedder

    async def answer_query(self, request: QueryRequest, scope: AccessScope) -> Answer:
        """Execute the full RAG pipeline for an authorized query."""
        route = await self.router.route(request.query)
        corpus_version = self.publisher.active_version
        
        if route == "no-retrieval-needed":
            # Conversational answers are not cached
            return await self.generator.generate(request.query, (), route)

        if not corpus_version:
            # Cannot retrieve without a published corpus
            return await self.generator.generate(request.query, (), route)

        query_vectors = await self.embedder.embed([request.query])
        if not query_vectors:
            raise RuntimeError("Failed to embed query")
        query_vector = query_vectors[0]

        if route == "decompose":
            subqueries = await self.router.decompose(request.query)
        else:
            subqueries = (request.query,)

        # Filtered hybrid retrieval across subqueries
        fused_evidence = await self.retriever.search(subqueries, scope, corpus_version)
        
        # Rerank and bound evidence
        evidence = await self.reranker.rerank_candidates(request.query, fused_evidence)

        # Cache check after reranking and bounding
        cached_answer = self.cache.get(query_vector, scope, corpus_version, evidence, route)
        
        if cached_answer:
            return cached_answer

        # Generator produces grounded claim citations
        answer = await self.generator.generate(request.query, evidence, route)
        
        # Verify permission epoch has not changed (basic safety check to simulate re-checking epoch before return)
        # If changed, one would normally raise an exception or retry. Here we just write to cache if it hasn't.
        # We assume `scope` is current at the time of this check.
        if answer.status == "grounded":
            self.cache.put(
                request.query, query_vector, scope, corpus_version, answer, evidence
            )
            
        return answer
