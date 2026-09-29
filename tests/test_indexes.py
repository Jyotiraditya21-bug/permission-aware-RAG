from src.indexes.dense import DenseIndex
from src.indexes.lexical import LexicalIndex
from src.models import AccessScope, Chunk, SourceACL


def make_acl(
    principals: tuple[str, ...] = ("user1",),
    groups: tuple[str, ...] = ("eng",),
    attributes: dict[str, tuple[str, ...]] | None = None,
) -> SourceACL:
    attrs = attributes or {}
    return SourceACL(
        principal_ids=frozenset(principals),
        group_ids=frozenset(groups),
        source_policy_attributes={k: frozenset(v) for k, v in attrs.items()},
        acl_version="v1",
    )


def make_scope(
    tenant_id: str = "tenant-a",
    principal_id: str = "user1",
    groups: tuple[str, ...] = ("eng",),
    attributes: dict[str, tuple[str, ...]] | None = None,
) -> AccessScope:
    attrs = attributes or {}
    return AccessScope(
        tenant_id=tenant_id,
        principal_id=principal_id,
        group_ids=frozenset(groups),
        source_policy_attributes={k: frozenset(v) for k, v in attrs.items()},
        permission_epoch=1,
    )


def make_chunk(
    chunk_id: str = "c1",
    text: str = "python 3.12 release notes",
    tenant_id: str = "tenant-a",
    acl: SourceACL | None = None,
) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        document_id="doc1",
        document_version="v1",
        text=text,
        source_locator="docs/1/doc1",
        tenant_id=tenant_id,
        acl=acl or make_acl(),
    )


def test_lexical_index_acl_filtering():
    lex_index = LexicalIndex()
    chunk1 = make_chunk(chunk_id="c1", text="fastapi python guide", acl=make_acl(principals=("user1",), groups=()))
    chunk2 = make_chunk(chunk_id="c2", text="fastapi security docs", acl=make_acl(principals=("user2",), groups=()))

    lex_index.publish_version("v1", [(chunk1, (0.1,)), (chunk2, (0.2,))])

    # Allowed scope user1
    scope_user1 = make_scope(principal_id="user1", groups=())
    results = lex_index.search(scope_user1, "v1", top_k=5, query_text="fastapi")
    assert len(results) == 1
    assert results[0][0].chunk_id == "c1"

    # Denied scope user3
    scope_user3 = make_scope(principal_id="user3", groups=())
    results_denied = lex_index.search(scope_user3, "v1", top_k=5, query_text="fastapi")
    assert len(results_denied) == 0

    # Wrong tenant
    scope_wrong_tenant = make_scope(tenant_id="tenant-b", principal_id="user1", groups=())
    assert len(lex_index.search(scope_wrong_tenant, "v1", top_k=5, query_text="fastapi")) == 0

    # Unknown corpus version
    assert len(lex_index.search(scope_user1, "v999", top_k=5, query_text="fastapi")) == 0


def test_dense_index_acl_filtering():
    dense_index = DenseIndex()
    vec1 = (1.0, 0.0, 0.0)
    vec2 = (0.0, 1.0, 0.0)

    chunk1 = make_chunk(chunk_id="c1", text="architecture summary", acl=make_acl(principals=("user1",), groups=()))
    chunk2 = make_chunk(chunk_id="c2", text="secret design", acl=make_acl(principals=("admin",), groups=()))

    dense_index.publish_version("v1", [(chunk1, vec1), (chunk2, vec2)])

    # Allowed user1
    scope_user1 = make_scope(principal_id="user1", groups=())
    results = dense_index.search(scope_user1, "v1", top_k=5, query_vector=(1.0, 0.0, 0.0))
    assert len(results) == 1
    assert results[0][0].chunk_id == "c1"
    assert results[0][1] > 0.99

    # Denied user2
    scope_user2 = make_scope(principal_id="user2", groups=())
    results_denied = dense_index.search(scope_user2, "v1", top_k=5, query_vector=(1.0, 0.0, 0.0))
    assert len(results_denied) == 0
