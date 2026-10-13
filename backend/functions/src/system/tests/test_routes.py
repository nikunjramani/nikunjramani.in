from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from shared.api import make_app
from src.system.routes import get_system_service, router

ADMIN = {"uid": "admin-1", "email": "admin@example.com", "admin": True}


def _client(fake: MagicMock) -> TestClient:
    app = make_app(router, "system-test")
    app.dependency_overrides[get_system_service] = lambda: fake
    return TestClient(app)


def test_audit_log_requires_admin() -> None:
    fake = MagicMock()
    assert _client(fake).get("/audit-log").status_code == 401
    fake.list_audit_log.assert_not_called()


def test_audit_log_passes_filters_through() -> None:
    fake = MagicMock()
    fake.list_audit_log.return_value = [{"id": "a1", "action": "update"}]
    with patch("shared.core.security.auth.verify_id_token", return_value=ADMIN):
        response = _client(fake).get(
            "/audit-log?collection=projects&docId=p1&limit=5",
            headers={"Authorization": "Bearer x"},
        )
    assert response.status_code == 200
    assert response.json() == [{"id": "a1", "action": "update"}]
    fake.list_audit_log.assert_called_once_with(collection="projects", doc_id="p1", limit=5)
