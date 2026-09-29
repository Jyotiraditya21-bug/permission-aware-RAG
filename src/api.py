"""Async FastAPI orchestration endpoints."""
from fastapi import Depends, FastAPI, HTTPException
from src.models import AccessScope, Answer, QueryRequest
from src.service import RAGService

app = FastAPI()

from fastapi import Depends, FastAPI, HTTPException, Request

from src.cache import SemanticCache
from src.generation import Generator
from src.indexes.dense import DenseIndex
from src.indexes.lexical import LexicalIndex
from src.ingestion.publication import Publisher
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.rerank import RerankingPipeline
from src.router import QueryRouter

# Dummy implementations for local dev
class DummyLLM:
    async def generate(self, prompt: str, text: str) -> str:
        return '[{"claim": "This is a dummy response.", "chunk_ids": []}]'

class DummyEmbedder:
    async def embed(self, texts: list[str]) -> tuple[tuple[float, ...], ...]:
        return tuple([(1.0, 0.0)] * len(texts))

class DummyReranker:
    async def rerank(self, query: str, texts: list[str]) -> tuple[float, ...]:
        return tuple([1.0] * len(texts))

# Singleton RAGService setup
lex = LexicalIndex()
den = DenseIndex()
publisher = Publisher(lex, den)
# For local dev we mock the publisher having an active corpus version
publisher._active_version = "v1"

retriever = HybridRetriever(lex, den, DummyEmbedder())
reranker = RerankingPipeline(DummyReranker())
router = QueryRouter(DummyLLM())
generator = Generator(DummyLLM())
cache = SemanticCache()

_service = RAGService(router, retriever, reranker, generator, cache, publisher, DummyEmbedder())

def get_service() -> RAGService:
    return _service

def get_access_scope(request: Request) -> AccessScope:
    # DEV ONLY - replace with real JWT validation before production
    user_id = request.headers.get("X-User-Id")
    tenant_id = request.headers.get("X-Tenant-Id")
    
    if not user_id or not tenant_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id or X-Tenant-Id header")
        
    return AccessScope(
        tenant_id=tenant_id,
        principal_id=user_id,
        group_ids=frozenset(),
        source_policy_attributes={},
        permission_epoch=1,
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/query", response_model=Answer)
async def query_endpoint(
    request: QueryRequest,
    scope: AccessScope = Depends(get_access_scope),
    service: RAGService = Depends(get_service),
) -> Answer:
    try:
        # Full RAG pipeline
        answer = await service.answer_query(request, scope)
        return answer
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
