import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from src.ingestion.sources import SourceBatch, normalize


def test_sources(record):
    for kind in ("docs", "tickets", "wikis"):
        data = dict(tenant_id="acme", source_id="handbook", source_type=kind,
                    change_token="c1", complete_snapshot=True,
                    records=[record.model_copy(update={"source_type": kind}).model_dump(mode="json")])
        batch = normalize(data)
        assert batch.records[0].content_hash != "untrusted"
        assert batch.complete_snapshot
        assert SourceBatch.model_validate_json(batch.model_dump_json()) == batch
        for bad in ({**data, "tenant_id": "other"}, {**data, "records": data["records"] * 2}):
            with pytest.raises(ValidationError):
                normalize(bad)
        del data["records"][0]["acl"]
        with pytest.raises(ValidationError):
            normalize(data)


def test_fixture_and_empty_live(record):
    assert normalize(json.loads(Path("tests/fixtures/sources.json").read_text())).records == ()
    data = dict(tenant_id="acme", source_id="handbook", source_type="docs", change_token="c2",
                records=[record.model_copy(update={"text": " "}).model_dump(mode="json")])
    with pytest.raises(ValidationError):
        normalize(data)
    data["records"][0]["deleted"] = True
    assert normalize(data).records[0].deleted
