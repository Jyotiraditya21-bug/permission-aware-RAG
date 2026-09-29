import pytest
from src.ingestion.chunking import chunk_record


def test_chunks(record):
    chunks = chunk_record(record, 3)
    assert len(chunks) == 2
    assert chunks == chunk_record(record, 3)
    assert chunks[0].acl == record.acl
    assert chunks[0].chunk_id != chunk_record(record.model_copy(update={"text": "new"}), 3)[0].chunk_id
    assert chunk_record(record.model_copy(update={"deleted": True})) == ()
    with pytest.raises(ValueError):
        chunk_record(record, 0)
