"""Lexical index adapter with pre-retrieval ACL filtering using BM25."""
from typing import Sequence
import rank_bm25

from src.acl import permitted
from src.models import AccessScope, Chunk


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in text.split() if token]


class LexicalIndex:
    def __init__(self) -> None:
        self._published: dict[str, tuple[tuple[Chunk, tuple[float, ...]], ...]] = {}

    def publish_version(
        self, corpus_version: str, chunks_with_vectors: Sequence[tuple[Chunk, tuple[float, ...]]]
    ) -> None:
        self._published[corpus_version] = tuple(chunks_with_vectors)

    def search(
        self,
        scope: AccessScope,
        corpus_version: str,
        top_k: int,
        query_text: str | None = None,
        query_vector: tuple[float, ...] | None = None,
    ) -> tuple[tuple[Chunk, float], ...]:
        if not query_text or top_k <= 0 or corpus_version not in self._published:
            return ()

        entries = self._published[corpus_version]
        # ACL filtering MUST happen BEFORE scoring/candidate selection
        permitted_chunks = [
            chunk for chunk, _ in entries
            if permitted(scope, chunk.tenant_id, chunk.acl)
        ]

        if not permitted_chunks:
            return ()

        corpus_tokens = [tokenize(c.text) for c in permitted_chunks]
        query_tokens = tokenize(query_text)
        if not query_tokens:
            return ()

        bm25 = rank_bm25.BM25Okapi(corpus_tokens)
        scores = bm25.get_scores(query_tokens)

        scored = list(zip(permitted_chunks, scores, strict=True))
        scored.sort(key=lambda item: item[1], reverse=True)
        return tuple((chunk, float(score)) for chunk, score in scored[:top_k])
