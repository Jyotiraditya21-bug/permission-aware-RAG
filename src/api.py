"""Async FastAPI orchestration endpoints with secure multi-tenant demonstration mode."""
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.acl import permitted
from src.cache import SemanticCache
from src.demo_corpus import DEMO_IDENTITIES, get_synthetic_chunks
from src.generation import Generator
from src.indexes.dense import DenseIndex
from src.indexes.lexical import LexicalIndex
from src.ingestion.publication import Publisher
from src.models import AccessScope, Answer, QueryRequest
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.rerank import RerankingPipeline
from src.router import QueryRouter
from src.service import RAGService

VERSION = "0.2.0"

app = FastAPI(
    title="Permission-Aware RAG API",
    description="Adaptive retrieval and grounded answers with pre-retrieval ACL enforcement",
    version=VERSION
)

# Restrict CORS to trusted production and development origins
DEFAULT_ORIGINS = [
    "https://jyotiraditya21-bug.github.io",
    "https://jyotiraditya.is-a.dev",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Deterministic Embedder & LLM for verifiable demonstration mode
class SyntheticDemoLLM:
    async def generate(self, prompt: str, text: str) -> str:
        # Grounded claim generator from evidence
        if "Chunk ID:" in prompt:
            # Extract citations from present chunks
            claims = []
            for line in prompt.split("\n"):
                if line.startswith("Chunk ID:"):
                    cid = line.replace("Chunk ID:", "").strip()
                    if "chunk-alpha-001" in cid:
                        claims.append({
                            "claim": "AlphaCorp Framework guarantees 99.99% SLA uptime across multi-cloud infrastructure.",
                            "chunk_ids": [cid]
                        })
                    elif "chunk-alpha-002" in cid:
                        claims.append({
                            "claim": "Project Titan is AlphaCorp's confidential Q4 initiative with $15M R&D allocation for zero-knowledge ACL vector indexes.",
                            "chunk_ids": [cid]
                        })
                    elif "chunk-beta-001" in cid:
                        claims.append({
                            "claim": "BetaLogistics partner guidelines mandate mTLS termination and AES-256 encrypted envelopes.",
                            "chunk_ids": [cid]
                        })
            if claims:
                import json
                return json.dumps(claims)
        return "[]"


class SyntheticDemoEmbedder:
    async def embed(self, texts: list[str]) -> tuple[tuple[float, ...], ...]:
        vectors = []
        for t in texts:
            # Simple deterministic 4-dimensional vector based on term frequency
            tl = t.lower()
            v0 = 1.0 if "alpha" in tl or "sla" in tl else 0.0
            v1 = 1.0 if "titan" in tl or "confidential" in tl else 0.0
            v2 = 1.0 if "beta" in tl or "partner" in tl else 0.0
            v3 = 1.0
            vectors.append((v0, v1, v2, v3))
        return tuple(vectors)


class SyntheticDemoReranker:
    async def rerank(self, query: str, texts: list[str]) -> tuple[float, ...]:
        return tuple([0.95 - (i * 0.1) for i in range(len(texts))])


# Initialize pipeline and singleton service
lex = LexicalIndex()
den = DenseIndex()
publisher = Publisher(lex, den)
embedder = SyntheticDemoEmbedder()
retriever = HybridRetriever(lex, den, embedder)
reranker = RerankingPipeline(SyntheticDemoReranker())
router = QueryRouter(SyntheticDemoLLM())
generator = Generator(SyntheticDemoLLM())
cache = SemanticCache()

_service = RAGService(router, retriever, reranker, generator, cache, publisher, embedder)

# Populate synthetic demonstration corpus
DEMO_CORPUS_VERSION = "v1"
synthetic_chunks = get_synthetic_chunks()
# Publish to both lexical and dense indexes
lex.publish_version(DEMO_CORPUS_VERSION, [(c, (1.0, 0.0, 0.0, 1.0)) for c in synthetic_chunks])
den.publish_version(DEMO_CORPUS_VERSION, [(c, (1.0, 0.0, 0.0, 1.0)) for c in synthetic_chunks])
publisher._active_version = DEMO_CORPUS_VERSION


def get_service() -> RAGService:
    return _service


def get_access_scope(request: Request) -> AccessScope:
    user_id = request.headers.get("X-User-Id")
    tenant_id = request.headers.get("X-Tenant-Id")
    
    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Fail-closed: Missing authenticated identity scope (X-User-Id and X-Tenant-Id required)"
        )
        
    return AccessScope(
        tenant_id=tenant_id,
        principal_id=user_id,
        group_ids=frozenset(),
        source_policy_attributes={},
        permission_epoch=1,
    )


# Standard Observability Endpoints
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Permission-Aware RAG",
        "version": VERSION,
        "corpus_version": publisher.active_version
    }


@app.get("/ready")
def readiness_check():
    if not publisher.active_version:
        raise HTTPException(status_code=503, detail="Corpus not published")
    return {"status": "ready"}


@app.get("/version")
def version_endpoint():
    return {
        "service": "permission-aware-RAG",
        "version": VERSION,
        "active_version": publisher.active_version
    }


# Demonstration Endpoints
class DemoQueryRequest(BaseModel):
    identity: str = Field(..., description="Demo persona (e.g. alice@alpha, bob@alpha, charlie@beta, anonymous)")
    query: str = Field(..., min_length=2, max_length=250, description="Search query")


@app.get("/demo/identities")
def list_demo_identities():
    """Returns available demonstration identities and their ACL scopes."""
    return [
        {
            "id": "alice@alpha",
            "name": "Alice (Admin & Engineering)",
            "tenant_id": "tenant_alpha",
            "groups": ["engineering", "admin", "all_alpha"],
            "description": "Full access to AlphaCorp public wikis and confidential engineering roadmap."
        },
        {
            "id": "bob@alpha",
            "name": "Bob (Sales Representative)",
            "tenant_id": "tenant_alpha",
            "groups": ["sales", "all_alpha"],
            "description": "Access to public AlphaCorp documents. Denied access to confidential engineering roadmap."
        },
        {
            "id": "charlie@beta",
            "name": "Charlie (Partner Contractor)",
            "tenant_id": "tenant_beta",
            "groups": ["contractors", "all_beta"],
            "description": "Access to Tenant Beta partner specifications. Strictly isolated from all Tenant Alpha records."
        },
        {
            "id": "anonymous",
            "name": "Anonymous / Unauthenticated",
            "tenant_id": "none",
            "groups": [],
            "description": "No valid token/identity. Demonstrates fail-closed zero-trust rejection."
        }
    ]


@app.post("/demo/query")
async def demo_query(req: DemoQueryRequest, response: Response, service: RAGService = Depends(get_service)):
    """
    Demonstration query endpoint showcasing pre-retrieval ACL filtering,
    cross-tenant isolation, and fail-closed security.
    """
    identity_key = req.identity.strip().lower()

    # Fail closed on missing/anonymous identity
    if identity_key == "anonymous" or identity_key not in DEMO_IDENTITIES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: Anonymous requests fail closed by default."
        )

    scope = DEMO_IDENTITIES[identity_key]

    # Pre-retrieval ACL audit: count total matching vs permitted chunks
    all_chunks = synthetic_chunks
    permitted_chunks = [c for c in all_chunks if permitted(scope, c.tenant_id, c.acl)]
    denied_count = len(all_chunks) - len(permitted_chunks)

    # Execute service pipeline
    query_obj = QueryRequest(query=req.query)
    answer = await service.answer_query(query_obj, scope)

    # Format authorized chunks
    authorized_chunks_data = [
        {
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "source_locator": c.source_locator,
            "text": c.text,
            "tenant_id": c.tenant_id
        }
        for c in permitted_chunks
        if req.query.lower() in c.text.lower() or any(w in c.text.lower() for w in req.query.lower().split() if len(w) > 3)
    ]

    return {
        "identity": identity_key,
        "tenant_id": scope.tenant_id,
        "groups": sorted(scope.group_ids),
        "query": req.query,
        "status": answer.status,
        "answer": answer.text,
        "citations": [
            {"claim": cite.claim, "chunk_ids": list(cite.chunk_ids)}
            for cite in answer.citations
        ],
        "authorized_chunks": authorized_chunks_data,
        "denied_chunks_count": denied_count,
        "route": answer.route,
        "trace_id": answer.trace_id
    }


# Standard query endpoint with scope dependency
@app.post("/query", response_model=Answer)
async def query_endpoint(
    request: QueryRequest,
    scope: AccessScope = Depends(get_access_scope),
    service: RAGService = Depends(get_service),
) -> Answer:
    try:
        answer = await service.answer_query(request, scope)
        return answer
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
