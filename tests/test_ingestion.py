from unittest.mock import AsyncMock
import pytest
from src.ingestion.pipeline import prepare, validate_vectors
from src.ingestion.state import change_kind, document_key


async def test_incremental(record):
    embedder = AsyncMock()
    embedder.embed.return_value = ((1.0, 0.0),)
    first = await prepare(record, None, embedder)
    assert document_key(record) != document_key(record.model_copy(update={"source_id": "other"}))
    assert change_kind(record, first) == "unchanged"
    assert await prepare(record, first, embedder) == first
    changed_acl = record.model_copy(update={"acl": record.acl.model_copy(update={"acl_version": "2"})})
    acl_only = await prepare(changed_acl, first, embedder)
    assert acl_only.chunks[0].acl.acl_version == "2"
    assert embedder.embed.await_count == 1
    second = await prepare(record.model_copy(update={"text": "New content"}), first, embedder)
    assert second.chunks[0].chunk_id != first.chunks[0].chunk_id
    deleted = await prepare(record.model_copy(update={"deleted": True}), second, embedder)
    assert not deleted.chunks and not deleted.vectors
    assert await prepare(deleted.record, deleted, embedder) == deleted


def test_vector_validation():
    validate_vectors((), 0)
    for vectors, count in [(((1.0,),), 2), (((),), 1), (((float("nan"),),), 1),
                           (((1.0,), (1.0, 2.0)), 2)]:
        with pytest.raises(ValueError):
            validate_vectors(vectors, count)
