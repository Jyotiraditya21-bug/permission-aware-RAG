"""Trusted bearer credentials mapped to immutable identity snapshots."""
import hashlib
import hmac

from src.models import AccessScope


class IdentityStore:
    def __init__(self, identities: dict[str, AccessScope]) -> None:
        self._identities = {
            hashlib.sha256(token.encode()).hexdigest(): scope.model_copy(deep=True)
            for token, scope in identities.items() if token
        }

    def resolve(self, token: str) -> AccessScope:
        digest = hashlib.sha256(token.encode()).hexdigest()
        for key, scope in self._identities.items():
            if hmac.compare_digest(key, digest):
                return scope.model_copy(deep=True)
        raise PermissionError("Unknown credential")

    def replace(self, token: str, scope: AccessScope | None) -> None:
        key = hashlib.sha256(token.encode()).hexdigest()
        previous = self._identities.get(key)
        if previous and scope and scope.permission_epoch <= previous.permission_epoch:
            raise ValueError("Permission changes require an advancing epoch")
        if scope is None:
            self._identities.pop(key, None)
        else:
            self._identities[key] = scope.model_copy(deep=True)

    def current(self, token: str, scope: AccessScope) -> bool:
        try:
            return self.resolve(token) == scope
        except PermissionError:
            return False
