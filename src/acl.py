"""Predicates are applied to metadata before scoring or content hydration."""
import hashlib
import json

from src.models import AccessScope, SourceACL


def permitted(scope: AccessScope, tenant_id: str, acl: SourceACL | None) -> bool:
    if acl is None or tenant_id != scope.tenant_id:
        return False
    grant = scope.principal_id in acl.principal_ids or bool(scope.group_ids & acl.group_ids)
    return grant and all(
        bool(values & scope.source_policy_attributes.get(key, frozenset()))
        for key, values in acl.source_policy_attributes.items()
    )


def fingerprint(scope: AccessScope) -> str:
    data = {
        "tenant": scope.tenant_id, "principal": scope.principal_id,
        "groups": sorted(scope.group_ids), "epoch": scope.permission_epoch,
        "attributes": {k: sorted(v) for k, v in scope.source_policy_attributes.items()},
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
