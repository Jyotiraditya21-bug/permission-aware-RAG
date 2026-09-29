import pytest

from src.models import AccessScope, SourceACL, SourceRecord


@pytest.fixture
def scope():
    return AccessScope(tenant_id="acme", principal_id="alice", group_ids={"staff"},
                       source_policy_attributes={"region": {"eu"}}, permission_epoch=1)


@pytest.fixture
def acl():
    return SourceACL(principal_ids={"alice"}, group_ids=set(),
                     source_policy_attributes={"region": {"eu"}}, acl_version="1")


@pytest.fixture
def record(acl):
    return SourceRecord(source_type="docs", source_id="handbook", document_id="vacation",
                        tenant_id="acme", text="Annual leave allowance is 25 days.",
                        modified_at="2026-09-29T00:00:00Z", content_hash="untrusted",
                        deleted=False, acl=acl)
