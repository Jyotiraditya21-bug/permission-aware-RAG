"""Deterministic non-overlapping word chunks with versioned identity."""
from src.ingestion.state import content_hash, document_key
from src.models import Chunk, SourceRecord


def chunk_record(record: SourceRecord, words_per_chunk: int = 180) -> tuple[Chunk, ...]:
    if words_per_chunk < 1:
        raise ValueError("Chunk size must be positive")
    if record.deleted:
        return ()
    version = content_hash(record.text)
    words = record.text.split()
    return tuple(Chunk(
        chunk_id=content_hash(f"{document_key(record)}:{version}:{words_per_chunk}:{offset}"),
        document_id=record.document_id, document_version=version,
        text=" ".join(words[offset:offset + words_per_chunk]),
        source_locator=f"{record.source_type}/{record.source_id}/{record.document_id}",
        tenant_id=record.tenant_id, acl=record.acl,
    ) for offset in range(0, len(words), words_per_chunk))
