"""Firebase Auth users — this subdomain's "collection". The only code touching the Auth
Admin SDK's user records; the `admin: true` custom claim is what authorises the panel."""

from __future__ import annotations

from dataclasses import dataclass

from firebase_admin import auth

from kernel.errors import NotFoundError
from kernel.firebase import ensure_app


@dataclass(frozen=True, slots=True)
class AuthUser:
    uid: str
    email: str | None
    display_name: str | None
    is_admin: bool
    claims: dict[str, object]


class AuthUserRepository:
    def __init__(self) -> None:
        ensure_app()

    def list_admins(self) -> list[AuthUser]:
        return [
            user
            for user in (self._to_user(u) for u in auth.list_users().iterate_all())
            if user.is_admin
        ]

    def get_by_email(self, email: str) -> AuthUser:
        try:
            return self._to_user(auth.get_user_by_email(email))
        except auth.UserNotFoundError as exc:
            raise NotFoundError(
                f"No user with email {email}. They must sign in to the site once first."
            ) from exc

    def get(self, uid: str) -> AuthUser:
        try:
            return self._to_user(auth.get_user(uid))
        except auth.UserNotFoundError as exc:
            raise NotFoundError(f"No user with uid {uid}.") from exc

    def set_claims(self, uid: str, claims: dict[str, object]) -> None:
        auth.set_custom_user_claims(uid, claims)

    def revoke_sessions(self, uid: str) -> None:
        """Kills refresh tokens; the panel's session check (checkRevoked) then fails."""
        auth.revoke_refresh_tokens(uid)

    @staticmethod
    def _to_user(record: auth.UserRecord) -> AuthUser:
        claims = dict(record.custom_claims or {})
        return AuthUser(
            uid=record.uid,
            email=record.email,
            display_name=record.display_name,
            is_admin=claims.get("admin") is True,
            claims=claims,
        )
