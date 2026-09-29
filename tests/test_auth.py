import pytest
from src.auth import IdentityStore


def test_identity_epoch_and_revocation(scope):
    store = IdentityStore({"secret": scope})
    assert store.resolve("secret") == scope
    with pytest.raises(PermissionError):
        store.resolve("forged")
    with pytest.raises(ValueError):
        store.replace("secret", scope)
    store.replace("secret", scope.model_copy(update={"permission_epoch": 2}))
    assert not store.current("secret", scope)
    store.replace("secret", None)
    assert not store.current("secret", scope)
