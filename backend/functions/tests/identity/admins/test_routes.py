from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from kernel.http import make_app
from src.identity.admins.repository import AuthUser
from src.identity.admins.routes import get_admin_access_service, router

ADMIN = {"uid": "me", "email": "me@example.com", "admin": True}
HEADERS = {"Authorization": "Bearer x"}


def _client(fake: MagicMock) -> TestClient:
    app = make_app(router, "admins-test")
    app.dependency_overrides[get_admin_access_service] = lambda: fake
    return TestClient(app)


def test_every_route_requires_admin() -> None:
    client = _client(MagicMock())
    assert client.get("/").status_code == 401
    assert client.post("/", json={"email": "a@example.com"}).status_code == 401
    assert client.delete("/u1").status_code == 401


def test_list_uses_camel_case() -> None:
    fake = MagicMock()
    fake.list_admins.return_value = [AuthUser("u1", "a@example.com", "Ana", True, {"admin": True})]
    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        response = _client(fake).get("/", headers=HEADERS)
    assert response.json() == [{"uid": "u1", "email": "a@example.com", "displayName": "Ana"}]


def test_grant_validates_the_email() -> None:
    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        response = _client(MagicMock()).post("/", json={"email": "not-an-email"}, headers=HEADERS)
    assert response.status_code == 422


def test_revoke_passes_the_caller_through() -> None:
    fake = MagicMock()
    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        response = _client(fake).delete("/u1", headers=HEADERS)
    assert response.status_code == 204
    fake.revoke.assert_called_once_with("u1", ADMIN)
