"""Dense index adapter with pre-retrieval ACL filtering."""
import math
from typing import Sequence

from src.acl import permitted
from src.models import AccessScope, Chunk


def cosine_similarity(v1: tuple[float, ...], v2: tuple[float, ...]) -> float:
    if len(v1) != len(v2) or not v1:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2, strict=True))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class DenseIndex:
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
        if not query_vector or top_k <= 0 or corpus_version not in self._published:
            return ()

        entries = self._published[corpus_version]
        # ACL filtering MUST happen BEFORE candidate selection & vector similarity computation
        permitted_entries = [
            (chunk, vector) for chunk, vector in entries
            if permitted(scope, chunk.tenant_id, chunk.acl)
        ]

        if not permitted_entries:
            return ()

        scored = [
            (chunk, cosine_similarity(query_vector, vector))
            for chunk, vector in permitted_entries
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return tuple(scored[:top_k])
