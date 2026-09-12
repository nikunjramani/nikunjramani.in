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


async def test_require_admin_returns_full_claims_for_the_audit_trail() -> None:
    with patch(
        "shared.core.security.auth.verify_id_token",
        return_value={"uid": "admin-1", "admin": True, "email": "admin@example.com"},
    ):
        claims = await require_admin("Bearer valid")
    assert claims["email"] == "admin@example.com"
