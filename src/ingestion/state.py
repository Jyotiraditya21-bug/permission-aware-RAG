"""Persistent publication payloads with stable source-qualified identity."""
import hashlib
import json

from src.models import Chunk, Contract, SourceRecord


class DocumentState(Contract):
    record: SourceRecord
    chunks: tuple[Chunk, ...]
    vectors: tuple[tuple[float, ...], ...]


def document_key(record: SourceRecord) -> str:
    return json.dumps([record.tenant_id, record.source_type, record.source_id, record.document_id])


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def change_kind(record: SourceRecord, previous: DocumentState | None) -> str:
    if previous and record.deleted == previous.record.deleted:
        if content_hash(record.text) == previous.record.content_hash:
            return "unchanged" if record.acl == previous.record.acl else "acl"
    return "delete" if record.deleted else "content"
