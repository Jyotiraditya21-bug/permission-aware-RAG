from src.acl import fingerprint, permitted


def test_predicate(scope, acl):
    assert permitted(scope, "acme", acl)
    assert not permitted(scope, "other", acl)
    assert not permitted(scope, "acme", None)
    for changes in ({"principal_ids": set()}, {"source_policy_attributes": {"unknown": {"x"}}},
                    {"source_policy_attributes": {"region": set()}}):
        assert not permitted(scope, "acme", acl.model_copy(update=changes))
    assert permitted(scope, "acme", acl.model_copy(update={"principal_ids": set(),
                                                          "group_ids": {"staff"}}))
    assert not permitted(scope.model_copy(update={"group_ids": set()}), "acme",
                         acl.model_copy(update={"principal_ids": set(), "group_ids": {"staff"}}))
    assert fingerprint(scope) == fingerprint(scope.model_copy(deep=True))
    assert fingerprint(scope) != fingerprint(scope.model_copy(update={"permission_epoch": 2}))
