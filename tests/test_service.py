import pytest
from src.cache import SemanticCache
from src.generation import Generator
from src.indexes.dense import DenseIndex
from src.indexes.lexical import LexicalIndex
from src.ingestion.publication import Publisher
from src.models import AccessScope, Answer, QueryRequest, RetrievalResult, Version
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.rerank import RerankingPipeline
from src.router import QueryRouter
from src.service import RAGService

class MockLLM:
    async def generate(self, prompt, text):
        return "direct-retrieve"

class MockEmbedder:
    async def embed(self, texts):
        return tuple([(1.0, 0.0)] * len(texts))

class MockGenerator(Generator):
    def __init__(self):
        pass
    async def generate(self, query, evidence, route):
        return Answer(
            status="abstained",
            text="answer",
            citations=(),
            route=route,
            trace_id="t1"
        )

@pytest.mark.asyncio
async def test_service_pipeline():
    router = QueryRouter(MockLLM())
    lex = LexicalIndex()
    den = DenseIndex()
    publisher = Publisher(lex, den)
    embedder = MockEmbedder()
    retriever = HybridRetriever(lex, den, embedder)
    
    class MockReranker:
        async def rerank(self, query, texts):
            return tuple([1.0] * len(texts))
            
    reranker = RerankingPipeline(MockReranker())
    generator = MockGenerator()
    cache = SemanticCache()
    
    service = RAGService(router, retriever, reranker, generator, cache, publisher, embedder)
    
    # Must have active corpus version
    req = QueryRequest(query="test")
    scope = AccessScope(tenant_id="t", principal_id="u", group_ids=frozenset(), source_policy_attributes={}, permission_epoch=1)
    
    ans = await service.answer_query(req, scope)
    assert ans.status == "abstained"
