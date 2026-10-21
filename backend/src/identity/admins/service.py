"""Admin access rules. A claim lands in the user's *next* ID token, so a grant takes effect
on their next sign-in; a revoke also kills their sessions so it takes effect at once."""

from __future__ import annotations

from kernel.audit import AuditWriter
from kernel.errors import ConflictError, ValidationError
from src.identity.admins.repository import AuthUser, AuthUserRepository

AUDIT_COLLECTION = "admins"


class AdminAccessService:
    def __init__(
        self,
        users: AuthUserRepository | None = None,
        audit: AuditWriter | None = None,
    ) -> None:
        self._users = users if users is not None else AuthUserRepository()
        self._audit = audit if audit is not None else AuditWriter()

    def list_admins(self) -> list[AuthUser]:
        return sorted(self._users.list_admins(), key=lambda u: (u.email or "", u.uid))

    def grant(self, email: str, claims: dict[str, object]) -> AuthUser:
        user = self._users.get_by_email(email)
        if user.is_admin:
            return user
        self._users.set_claims(user.uid, {**user.claims, "admin": True})
        self._record(user, claims, granted=True)
        return self._users.get(user.uid)

    def revoke(self, uid: str, claims: dict[str, object]) -> None:
        if uid == claims.get("uid"):
            raise ValidationError("You can't remove your own admin access.")
        user = self._users.get(uid)
        if not user.is_admin:
            return
        if len(self._users.list_admins()) <= 1:
            raise ConflictError("Refusing to remove the last admin.")
        remaining = {k: v for k, v in user.claims.items() if k != "admin"}
        self._users.set_claims(uid, remaining)
        self._users.revoke_sessions(uid)
        self._record(user, claims, granted=False)

    def _record(self, user: AuthUser, claims: dict[str, object], *, granted: bool) -> None:
        self._audit.record(
            claims=claims,
            action="update",
            collection=AUDIT_COLLECTION,
            doc_id=user.uid,
            before={"email": user.email, "admin": not granted},
            after={"email": user.email, "admin": granted},
        )
