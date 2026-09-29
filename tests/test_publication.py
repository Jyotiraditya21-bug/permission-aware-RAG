from datetime import datetime, timezone
import pytest

from src.indexes.dense import DenseIndex
from src.indexes.lexical import LexicalIndex
from src.ingestion.publication import PublicationError, Publisher
from src.ingestion.state import DocumentState
from src.models import AccessScope, Chunk, SourceACL, SourceRecord


def make_acl(principals=("user1",)) -> SourceACL:
    return SourceACL(
        principal_ids=frozenset(principals),
        group_ids=frozenset(),
        source_policy_attributes={},
        acl_version="v1",
    )


def make_scope(principal_id="user1") -> AccessScope:
    return AccessScope(
        tenant_id="tenant-a",
        principal_id=principal_id,
        group_ids=frozenset(),
        source_policy_attributes={},
        permission_epoch=1,
    )


def make_record(doc_id="doc1", deleted=False, acl=None) -> SourceRecord:
    return SourceRecord(
        source_type="docs",
        source_id="src1",
        document_id=doc_id,
        tenant_id="tenant-a",
        text="python async architecture",
        modified_at=datetime.now(timezone.utc),
        content_hash="hash1",
        deleted=deleted,
        acl=acl or make_acl(),
    )


def make_state(doc_id="doc1", chunk_id="c1", deleted=False, acl=None) -> DocumentState:
    record = make_record(doc_id=doc_id, deleted=deleted, acl=acl)
    chunk = Chunk(
        chunk_id=chunk_id,
        document_id=doc_id,
        document_version="v1",
        text=record.text,
        source_locator=f"docs/src1/{doc_id}",
        tenant_id="tenant-a",
        acl=record.acl,
    )
    return DocumentState(
        record=record,
        chunks=() if deleted else (chunk,),
        vectors=() if deleted else ((1.0, 0.0),),
    )


class FailingIndex(LexicalIndex):
    def publish_version(self, corpus_version, chunks_with_vectors):
        raise RuntimeError("Index publishing failed")


def test_staged_dual_index_publication():
    lex_index = LexicalIndex()
    dense_index = DenseIndex()
    publisher = Publisher(lex_index, dense_index)

    state1 = make_state(doc_id="doc1", chunk_id="c1")
    publisher.publish([state1], "corpus-v1")

    assert publisher.active_version == "corpus-v1"

    scope = make_scope("user1")
    lex_res = lex_index.search(scope, "corpus-v1", top_k=5, query_text="python")
    dense_res = dense_index.search(scope, "corpus-v1", top_k=5, query_vector=(1.0, 0.0))

    assert len(lex_res) == 1
    assert len(dense_res) == 1
    assert lex_res[0][0].chunk_id == "c1"


def test_publication_failure_rolls_back():
    failing_lex = FailingIndex()
    dense_index = DenseIndex()
    publisher = Publisher(failing_lex, dense_index)

    state1 = make_state(doc_id="doc1", chunk_id="c1")

    with pytest.raises(PublicationError):
        publisher.publish([state1], "corpus-v1")

    assert publisher.active_version is None


def test_publication_deletion_and_revocation():
    lex_index = LexicalIndex()
    dense_index = DenseIndex()
    publisher = Publisher(lex_index, dense_index)

    # Initial publish doc1
    state1 = make_state(doc_id="doc1", chunk_id="c1", acl=make_acl(principals=("user1",)))
    publisher.publish([state1], "v1")

    # Revocation: update ACL for doc1 to user2 only
    state1_revoked = make_state(doc_id="doc1", chunk_id="c1", acl=make_acl(principals=("user2",)))
    publisher.publish([state1_revoked], "v2")

    assert publisher.active_version == "v2"
    # user1 can no longer access v2
    assert len(lex_index.search(make_scope("user1"), "v2", top_k=5, query_text="python")) == 0
    # user2 can access v2
    assert len(lex_index.search(make_scope("user2"), "v2", top_k=5, query_text="python")) == 1

    # Deletion: tombstone doc1
    state1_deleted = make_state(doc_id="doc1", chunk_id="c1", deleted=True)
    publisher.publish([state1_deleted], "v3")

    assert publisher.active_version == "v3"
    assert len(lex_index.search(make_scope("user2"), "v3", top_k=5, query_text="python")) == 0
