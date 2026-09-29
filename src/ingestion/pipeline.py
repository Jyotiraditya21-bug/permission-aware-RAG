"""Prepare an update without mutating the published corpus."""
import math
from typing import Protocol, Sequence

from src.ingestion.chunking import chunk_record
from src.ingestion.state import DocumentState, change_kind, content_hash
from src.models import SourceRecord


class Embedder(Protocol):
    async def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]: ...


def validate_vectors(vectors: tuple[tuple[float, ...], ...], count: int) -> None:
    if len(vectors) != count or any(
        not vector or not all(math.isfinite(value) for value in vector) for vector in vectors
    ) or len({len(vector) for vector in vectors}) > 1:
        raise ValueError("Invalid embedding response")


async def prepare(
    record: SourceRecord, previous: DocumentState | None, embedder: Embedder,
    words_per_chunk: int = 180,
) -> DocumentState:
    kind = change_kind(record, previous)
    record = record.model_copy(update={"content_hash": content_hash(record.text)})
    if kind == "unchanged" and previous is not None:
        return previous
    if kind == "acl" and previous is not None:
        return DocumentState(record=record, chunks=tuple(
            chunk.model_copy(update={"acl": record.acl}) for chunk in previous.chunks
        ), vectors=previous.vectors)
    chunks = chunk_record(record, words_per_chunk)
    vectors = await embedder.embed([chunk.text for chunk in chunks]) if chunks else ()
    validate_vectors(vectors, len(chunks))
    return DocumentState(record=record, chunks=chunks, vectors=vectors)
