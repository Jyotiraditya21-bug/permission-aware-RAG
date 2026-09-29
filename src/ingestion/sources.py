"""Normalized JSON export boundary for docs, tickets, and wikis."""
import hashlib
from typing import Literal

from pydantic import Field, model_validator
from typing_extensions import Self

from src.models import Contract, NonEmptyText, SourceRecord


class SourceBatch(Contract):
    tenant_id: NonEmptyText
    source_id: NonEmptyText
    source_type: Literal["docs", "tickets", "wikis"]
    change_token: NonEmptyText
    complete_snapshot: bool = False
    records: tuple[SourceRecord, ...] = Field(max_length=10000)

    @model_validator(mode="after")
    def validate_boundary(self) -> Self:
        seen: set[str] = set()
        for record in self.records:
            if (record.tenant_id, record.source_id, record.source_type) != (
                self.tenant_id, self.source_id, self.source_type
            ):
                raise ValueError("Record outside source boundary")
            if record.document_id in seen:
                raise ValueError("Duplicate source document")
            seen.add(record.document_id)
            if not record.deleted and not record.text.strip():
                raise ValueError("Live documents need content")
        return self


def normalize(payload: dict[str, object]) -> SourceBatch:
    batch = SourceBatch.model_validate(payload)
    return batch.model_copy(update={"records": tuple(
        record.model_copy(update={"content_hash": hashlib.sha256(record.text.encode()).hexdigest()})
        for record in batch.records
    )})
