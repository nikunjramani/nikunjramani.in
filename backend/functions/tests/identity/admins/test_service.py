"""AdminAccessService against an in-memory user store — the guards are the point."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import MagicMock

import pytest

from kernel.errors import ConflictError, NotFoundError, ValidationError
from src.identity.admins.repository import AuthUser
from src.identity.admins.service import AdminAccessService

ME = {"uid": "me", "email": "me@example.com", "admin": True}


class FakeUsers:
    def __init__(self, *users: AuthUser) -> None:
        self.users = {u.uid: u for u in users}
        self.revoked: list[str] = []

    def list_admins(self) -> list[AuthUser]:
        return [u for u in self.users.values() if u.is_admin]

    def get(self, uid: str) -> AuthUser:
        if uid not in self.users:
            raise NotFoundError(uid)
        return self.users[uid]

    def get_by_email(self, email: str) -> AuthUser:
        for user in self.users.values():
            if user.email == email:
                return user
        raise NotFoundError(email)

    def set_claims(self, uid: str, claims: dict[str, object]) -> None:
        self.users[uid] = replace(
            self.users[uid], claims=claims, is_admin=claims.get("admin") is True
        )

    def revoke_sessions(self, uid: str) -> None:
        self.revoked.append(uid)


def _user(uid: str, *, admin: bool, **claims: object) -> AuthUser:
    all_claims = {**claims, **({"admin": True} if admin else {})}
    return AuthUser(uid, f"{uid}@example.com", None, admin, all_claims)


def _service(users: FakeUsers) -> tuple[AdminAccessService, MagicMock]:
    audit = MagicMock()
    return AdminAccessService(users=users, audit=audit), audit  # type: ignore[arg-type]


def test_grant_sets_the_claim_and_keeps_other_claims() -> None:
    users = FakeUsers(_user("me", admin=True), _user("ana", admin=False, beta=True))
    svc, audit = _service(users)
    granted = svc.grant("ana@example.com", ME)
    assert granted.is_admin
    assert users.users["ana"].claims == {"beta": True, "admin": True}
    assert audit.record.call_args.kwargs["after"] == {"email": "ana@example.com", "admin": True}


def test_granting_an_existing_admin_is_a_no_op() -> None:
    users = FakeUsers(_user("me", admin=True))
    svc, audit = _service(users)
    svc.grant("me@example.com", ME)
    audit.record.assert_not_called()


def test_grant_for_an_unknown_email_is_404() -> None:
    svc, _ = _service(FakeUsers(_user("me", admin=True)))
    with pytest.raises(NotFoundError):
        svc.grant("nobody@example.com", ME)


def test_revoke_removes_the_claim_and_kills_sessions() -> None:
    users = FakeUsers(_user("me", admin=True), _user("ana", admin=True))
    svc, audit = _service(users)
    svc.revoke("ana", ME)
    assert not users.users["ana"].is_admin
    assert users.revoked == ["ana"]
    audit.record.assert_called_once()


def test_you_cannot_revoke_yourself() -> None:
    svc, _ = _service(FakeUsers(_user("me", admin=True), _user("ana", admin=True)))
    with pytest.raises(ValidationError):
        svc.revoke("me", ME)


def test_the_last_admin_cannot_be_removed() -> None:
    # "me" is no longer an admin (e.g. revoked elsewhere) but still holds a valid token.
    users = FakeUsers(_user("me", admin=False), _user("ana", admin=True))
    svc, _ = _service(users)
    with pytest.raises(ConflictError):
        svc.revoke("ana", ME)
    assert users.users["ana"].is_admin


def test_admins_are_listed_by_email() -> None:
    users = FakeUsers(_user("zed", admin=True), _user("amy", admin=True), _user("bob", admin=False))
    svc, _ = _service(users)
    assert [u.uid for u in svc.list_admins()] == ["amy", "zed"]
