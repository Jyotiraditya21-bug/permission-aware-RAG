"""Async FastAPI orchestration endpoints."""
from fastapi import Depends, FastAPI, HTTPException
from src.models import AccessScope, Answer, QueryRequest
from src.service import RAGService

app = FastAPI()

def get_service() -> RAGService:
    # Dependency injection placeholder
    raise NotImplementedError()

def get_access_scope() -> AccessScope:
    # Authentication dependency placeholder
    raise NotImplementedError()

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
