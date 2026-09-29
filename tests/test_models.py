import unittest

from pydantic import ValidationError

from src.models import (
    AccessScope, Answer, Chunk, Citation, Contract, QueryRequest,
    RetrievalResult, SourceACL, SourceRecord, Version,
)


ACL = {
    "principal_ids": ["user-1"], "group_ids": [],
    "source_policy_attributes": {}, "acl_version": "acl-1",
}
VERSION = {
    "document_version": "doc-v1", "corpus_version": "corpus-1", "acl_version": "acl-1",
}
SCOPE = {
    "tenant_id": "tenant-1", "principal_id": "user-1", "group_ids": [],
    "source_policy_attributes": {}, "permission_epoch": 0,
}
SOURCE = {
    "source_type": "docs", "source_id": "source-1", "document_id": "doc-1",
    "tenant_id": "tenant-1", "text": "Evidence", "modified_at": "2026-09-29T10:00:00Z",
    "content_hash": "hash-1", "deleted": False, "acl": ACL,
}
CHUNK = {
    "chunk_id": "chunk-1", "document_id": "doc-1", "document_version": "doc-v1",
    "text": "Evidence", "source_locator": "docs/doc-1", "tenant_id": "tenant-1", "acl": ACL,
}
RESULT = {
    "chunk_id": "chunk-1", "text": "Evidence", "version": VERSION, "fusion_rank": 1,
}
CITATION = {"claim": "Supported claim", "chunk_ids": ["chunk-1"]}
ANSWER = {
    "status": "grounded", "text": "Supported claim", "citations": [CITATION],
    "route": "direct-retrieve", "trace_id": "trace-1",
}


class ModelTests(unittest.TestCase):
    def test_contract_round_trips_and_forbids_extra_fields(self) -> None:
        for model, data in (
            (Contract, {}), (QueryRequest, {"query": "Question?"}), (AccessScope, SCOPE),
            (SourceACL, ACL), (Version, VERSION), (SourceRecord, SOURCE),
            (Chunk, CHUNK), (RetrievalResult, RESULT), (Citation, CITATION), (Answer, ANSWER),
        ):
            with self.subTest(model=model.__name__):
                instance = model.model_validate(data)
                self.assertEqual(model.model_validate_json(instance.model_dump_json()), instance)
                with self.assertRaises(ValidationError):
                    model.model_validate({**data, "unexpected": True})

    def test_query_rejects_empty_text_and_client_identity(self) -> None:
        for text in ("", "  \n", None, 123):
            with self.subTest(text=text), self.assertRaises(ValidationError):
                QueryRequest(query=text)
        for field in ("tenant_id", "principal_id", "group_ids", "access_scope", "permission_epoch"):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                QueryRequest.model_validate({"query": "Question?", field: "forged"})

    def test_access_metadata_is_required(self) -> None:
        for model, data, fields in (
            (AccessScope, SCOPE, tuple(SCOPE)), (SourceACL, ACL, tuple(ACL)),
            (SourceRecord, SOURCE, ("tenant_id", "acl")), (Chunk, CHUNK, ("tenant_id", "acl")),
        ):
            for field in fields:
                for missing in (True, False):
                    invalid = dict(data)
                    if missing:
                        invalid.pop(field)
                    else:
                        invalid[field] = None
                    with self.subTest(model=model.__name__, field=field, missing=missing):
                        with self.assertRaises(ValidationError):
                            model.model_validate(invalid)
        denied = SourceACL.model_validate({**ACL, "principal_ids": []})
        self.assertFalse(denied.principal_ids | denied.group_ids)

    def test_invalid_contract_values(self) -> None:
        for model, data, field, values in (
            (AccessScope, SCOPE, "permission_epoch", (-1, True, "1")),
            (AccessScope, SCOPE, "group_ids", ([""],)),
            (SourceACL, ACL, "source_policy_attributes", ({"": []}, {"role": [""]})),
            (SourceRecord, SOURCE, "source_type", ("unknown",)),
            (SourceRecord, SOURCE, "modified_at", ("2026-09-29T10:00:00", "invalid")),
            (SourceRecord, SOURCE, "deleted", ("false", 1)),
            (SourceRecord, SOURCE, "content_hash", ("",)),
            (Chunk, CHUNK, "chunk_id", ("",)),
            (Chunk, CHUNK, "text", (" ",)),
            (Chunk, CHUNK, "document_version", ("",)),
            (RetrievalResult, RESULT, "fusion_rank", (0, -1, True, 1.5)),
            (Citation, CITATION, "chunk_ids", ([], [""])),
            (Citation, CITATION, "claim", ("",)),
            (Answer, ANSWER, "status", ("invalid",)),
            (Answer, ANSWER, "route", ("invalid",)),
            (Answer, ANSWER, "trace_id", ("",)),
        ):
            for value in values:
                with self.subTest(model=model.__name__, field=field, value=value):
                    with self.assertRaises(ValidationError):
                        model.model_validate({**data, field: value})

    def test_source_types_and_tombstone(self) -> None:
        for source_type in ("docs", "tickets", "wikis"):
            record = SourceRecord.model_validate({**SOURCE, "source_type": source_type})
            self.assertEqual(record.source_type, source_type)
        tombstone = SourceRecord.model_validate({**SOURCE, "deleted": True, "text": ""})
        self.assertTrue(tombstone.deleted)

    def test_versions_required_and_nonblank(self) -> None:
        for field in VERSION:
            invalid = dict(VERSION)
            invalid.pop(field)
            with self.subTest(field=field), self.assertRaises(ValidationError):
                Version.model_validate(invalid)
            with self.assertRaises(ValidationError):
                Version.model_validate({**VERSION, field: " "})

    def test_chunk_identity_is_frozen(self) -> None:
        chunk = Chunk.model_validate(CHUNK)
        with self.assertRaises(ValidationError):
            chunk.chunk_id = "replacement"

    def test_scores_are_optional_and_finite(self) -> None:
        for field in ("lexical_score", "dense_score", "rerank_score"):
            for value in (None, -0.5, 0, 1.5):
                result = RetrievalResult.model_validate({**RESULT, field: value})
                self.assertEqual(getattr(result, field), value)
            for value in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                    RetrievalResult.model_validate({**RESULT, field: value})

    def test_answer_grounding_shapes(self) -> None:
        for status in ("grounded", "abstained", "conversational"):
            for route in ("direct-retrieve", "decompose", "no-retrieval-needed"):
                for citations in ([], [CITATION]):
                    valid = (
                        (status == "grounded" and bool(citations) and route != "no-retrieval-needed")
                        or (status == "abstained" and not citations)
                        or (status == "conversational" and not citations and route == "no-retrieval-needed")
                    )
                    data = {**ANSWER, "status": status, "route": route, "citations": citations}
                    with self.subTest(status=status, route=route, citations=citations):
                        if valid:
                            self.assertEqual(Answer.model_validate(data).status, status)
                        else:
                            with self.assertRaises(ValidationError):
                                Answer.model_validate(data)
