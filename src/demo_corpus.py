"""
Synthetic multi-tenant demonstration corpus for Permission-Aware RAG.
Contains strictly non-sensitive, synthetic enterprise documents:
- Tenant alpha: public overview (all alpha), confidential roadmap (engineering only)
- Tenant beta: partner guidelines (beta only)
"""
from src.models import AccessScope, Chunk, SourceACL

# 1. Demonstration Identities
DEMO_IDENTITIES: dict[str, AccessScope] = {
    "alice@alpha": AccessScope(
        tenant_id="tenant_alpha",
        principal_id="alice@alpha.com",
        group_ids=frozenset(["engineering", "admin", "all_alpha"]),
        source_policy_attributes={"classification": frozenset(["public", "confidential"])},
        permission_epoch=1
    ),
    "bob@alpha": AccessScope(
        tenant_id="tenant_alpha",
        principal_id="bob@alpha.com",
        group_ids=frozenset(["sales", "all_alpha"]),
        source_policy_attributes={"classification": frozenset(["public"])},
        permission_epoch=1
    ),
    "charlie@beta": AccessScope(
        tenant_id="tenant_beta",
        principal_id="charlie@beta.com",
        group_ids=frozenset(["contractors", "all_beta"]),
        source_policy_attributes={"classification": frozenset(["public", "partner"])},
        permission_epoch=1
    )
}

# 2. Synthetic Corpus Chunks
def get_synthetic_chunks() -> list[Chunk]:
    # Doc 1: Alpha Public Overview
    acl_alpha_public = SourceACL(
        principal_ids=frozenset(),
        group_ids=frozenset(["all_alpha"]),
        source_policy_attributes={"classification": frozenset(["public"])},
        acl_version="acl-v1"
    )
    chunk_1 = Chunk(
        chunk_id="chunk-alpha-001",
        document_id="doc-alpha-overview",
        document_version="doc-v1",
        text="AlphaCorp Enterprise AI Framework provides 99.99% SLA uptime and real-time inference across multi-cloud regions.",
        source_locator="wiki://alpha/overview.md",
        tenant_id="tenant_alpha",
        acl=acl_alpha_public
    )

    # Doc 2: Alpha Confidential Project Titan (Restricted to engineering)
    acl_alpha_engineering = SourceACL(
        principal_ids=frozenset(["alice@alpha.com"]),
        group_ids=frozenset(["engineering"]),
        source_policy_attributes={"classification": frozenset(["confidential"])},
        acl_version="acl-v1"
    )
    chunk_2 = Chunk(
        chunk_id="chunk-alpha-002",
        document_id="doc-alpha-titan",
        document_version="doc-v1",
        text="Project Titan Strategy: AlphaCorp's confidential Q4 initiative deploying zero-knowledge ACL vector indexes with $15M R&D capital allocation.",
        source_locator="docs://alpha/confidential/project_titan.md",
        tenant_id="tenant_alpha",
        acl=acl_alpha_engineering
    )

    # Doc 3: Beta Partner Guidelines (Tenant beta only)
    acl_beta_partner = SourceACL(
        principal_ids=frozenset(),
        group_ids=frozenset(["all_beta", "contractors"]),
        source_policy_attributes={"classification": frozenset(["partner"])},
        acl_version="acl-v1"
    )
    chunk_3 = Chunk(
        chunk_id="chunk-beta-001",
        document_id="doc-beta-partner-spec",
        document_version="doc-v1",
        text="BetaLogistics Partner Specification: External logistics webhooks must terminate with mTLS and AES-256 encrypted payload envelopes.",
        source_locator="docs://beta/partner_spec.md",
        tenant_id="tenant_beta",
        acl=acl_beta_partner
    )

    return [chunk_1, chunk_2, chunk_3]
