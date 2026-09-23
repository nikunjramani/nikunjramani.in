"""require_admin, proven once here rather than for the first time by whichever content
domain happens to be built first. Every future admin route depends on this working."""

from __future__ import annotations

from unittest.mock import patch

from fastapi import APIRouter
from fastapi.testclient import TestClient

from shared.api import make_app
from shared.core.security import AdminClaims, require_admin

router = APIRouter()


@router.get("/protected")
async def protected(claims: AdminClaims) -> dict[str, object]:
    return {"uid": claims["uid"]}


def _client() -> TestClient:
    # make_app(), not a bare FastAPI() — the DomainError -> JSON-with-status-code
    # translation these tests are actually checking lives in that wiring, not in FastAPI
    # itself. A bare app would let AuthError/PermissionDeniedError propagate unhandled.
    return TestClient(make_app(router, "security-test"))


def test_no_token_is_401() -> None:
    response = _client().get("/protected")
    assert response.status_code == 401


def test_malformed_header_is_401() -> None:
    response = _client().get("/protected", headers={"Authorization": "not-a-bearer-token"})
    assert response.status_code == 401


def test_invalid_token_is_401() -> None:
    with patch("shared.core.security.auth.verify_id_token", side_effect=ValueError("bad token")):
        response = _client().get("/protected", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401


def test_valid_token_without_admin_claim_is_403() -> None:
    with patch(
        "shared.core.security.auth.verify_id_token",
        return_value={"uid": "user-1", "admin": False},
    ):
        response = _client().get("/protected", headers={"Authorization": "Bearer valid"})
    assert response.status_code == 403


def test_valid_token_with_admin_claim_is_200() -> None:
    with patch(
        "shared.core.security.auth.verify_id_token",
        return_value={"uid": "admin-1", "admin": True},
    ):
        response = _client().get("/protected", headers={"Authorization": "Bearer valid"})
    assert response.status_code == 200
    assert response.json() == {"uid": "admin-1"}


def test_verify_token_ensures_a_firebase_app_exists_before_verifying() -> None:
    """Regression test for a real bug, not a hypothetical one: require_admin runs before
    any route body, so on a cold instance it's often the *first* Admin SDK call of the
    whole request — nothing has necessarily called get_db() yet to create the default app
    as a side effect. Without an explicit ensure_app() call first, verify_id_token raises
    "the default Firebase app does not exist", indistinguishable from a bad token once the
    broad except in verify_token wraps it as AuthError. Every other test in this file mocks
    auth.verify_id_token directly, which is exactly why none of them caught this — it only
    showed up testing against a genuinely cold Functions emulator, where every single
    admin-gated request failed with "Invalid or expired token" no matter how fresh the
    token actually was."""
    call_order: list[str] = []

    def _ensure_app() -> None:
        call_order.append("ensure_app")

    def _verify_id_token(token: str) -> dict[str, object]:
        call_order.append("verify_id_token")
        return {"uid": "admin-1", "admin": True}

    with (
        patch("shared.core.security.ensure_app", side_effect=_ensure_app),
        patch("shared.core.security.auth.verify_id_token", side_effect=_verify_id_token),
    ):
        response = _client().get("/protected", headers={"Authorization": "Bearer valid"})
    assert response.status_code == 200
    assert call_order == ["ensure_app", "verify_id_token"]


async def test_require_admin_returns_full_claims_for_the_audit_trail() -> None:
    with patch(
        "shared.core.security.auth.verify_id_token",
        return_value={"uid": "admin-1", "admin": True, "email": "admin@example.com"},
    ):
        claims = await require_admin("Bearer valid")
    assert claims["email"] == "admin@example.com"
