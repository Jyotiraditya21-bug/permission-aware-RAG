"""Base contract and protocols for ACL-filtered index adapters."""
from typing import Protocol, Sequence

from src.models import AccessScope, Chunk


class IndexBackend(Protocol):
    def publish_version(
        self, corpus_version: str, chunks_with_vectors: Sequence[tuple[Chunk, tuple[float, ...]]]
    ) -> None:
        ...

    def search(
        self,
        scope: AccessScope,
        corpus_version: str,
        top_k: int,
        query_text: str | None = None,
        query_vector: tuple[float, ...] | None = None,
    ) -> tuple[tuple[Chunk, float], ...]:
        ...
