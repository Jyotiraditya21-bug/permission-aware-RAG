"""Semantic answer caching with exact scope and evidence compatibility."""
import time
from typing import Sequence
from src.acl import fingerprint
from src.indexes.dense import cosine_similarity
from src.models import AccessScope, Answer, Route, RetrievalResult


class CacheEntry:
    def __init__(
        self,
        query: str,
        query_vector: tuple[float, ...],
        scope_fingerprint: str,
        corpus_version: str,
        answer: Answer,
        evidence_ids: frozenset[str],
        expires_at: float,
        route: Route,
    ):
        self.query = query
        self.query_vector = query_vector
        self.scope_fingerprint = scope_fingerprint
        self.corpus_version = corpus_version
        self.answer = answer
        self.evidence_ids = evidence_ids
        self.expires_at = expires_at
        self.route = route


class SemanticCache:
    def __init__(self, similarity_threshold: float = 0.95, default_ttl_sec: float = 3600.0) -> None:
        self._entries: list[CacheEntry] = []
        self.similarity_threshold = similarity_threshold
        self.default_ttl_sec = default_ttl_sec

    def put(
        self,
        query: str,
        query_vector: tuple[float, ...],
        scope: AccessScope,
        corpus_version: str,
        answer: Answer,
        evidence: Sequence[RetrievalResult],
        ttl_sec: float | None = None,
    ) -> None:
        if answer.status != "grounded":
            return
            
        ttl = ttl_sec if ttl_sec is not None else self.default_ttl_sec
        expires_at = time.time() + ttl
        
        evidence_ids = frozenset(c.chunk_id for c in evidence)
        entry = CacheEntry(
            query=query,
            query_vector=query_vector,
            scope_fingerprint=fingerprint(scope),
            corpus_version=corpus_version,
            answer=answer,
            evidence_ids=evidence_ids,
            expires_at=expires_at,
            route=answer.route,
        )
        self._entries.append(entry)

    def get(
        self,
        query_vector: tuple[float, ...],
        scope: AccessScope,
        corpus_version: str,
        current_evidence: Sequence[RetrievalResult],
        route: Route,
    ) -> Answer | None:
        now = time.time()
        scope_fp = fingerprint(scope)
        current_evidence_ids = frozenset(c.chunk_id for c in current_evidence)
        
        best_entry = None
        best_sim = -1.0
        
        for entry in self._entries:
            if entry.expires_at < now:
                continue
            if entry.scope_fingerprint != scope_fp:
                continue
            if entry.corpus_version != corpus_version:
                continue
            if entry.route != route:
                continue
                
            sim = cosine_similarity(query_vector, entry.query_vector)
            if sim >= self.similarity_threshold and sim > best_sim:
                best_entry = entry
                best_sim = sim
                
        if not best_entry:
            return None
            
        for citation in best_entry.answer.citations:
            if not frozenset(citation.chunk_ids).issubset(current_evidence_ids):
                return None
                
        return best_entry.answer
