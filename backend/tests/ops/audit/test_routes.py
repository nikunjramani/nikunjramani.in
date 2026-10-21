from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from kernel.app import make_app
from kernel.records import Record
from shared.generated import AuditLog
from src.ops.audit.routes import get_audit_service, router

ADMIN = {"uid": "admin-1", "email": "admin@example.com", "admin": True}


def _client(fake: MagicMock) -> TestClient:
    app = make_app(router, "audit-test")
    app.dependency_overrides[get_audit_service] = lambda: fake
    return TestClient(app)


def test_audit_log_requires_admin() -> None:
    fake = MagicMock()
    assert _client(fake).get("/").status_code == 401
    fake.list_entries.assert_not_called()


def test_audit_log_passes_filters_through() -> None:
    fake = MagicMock()
    entry = AuditLog.model_validate(
        {
            "actor": "u1",
            "action": "update",
            "collection": "projects",
            "docId": "p1",
            "at": "2026-01-03T00:00:00Z",
        }
    )
    fake.list_entries.return_value = [Record(id="a1", data=entry)]
    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        response = _client(fake).get(
            "/?collection=projects&docId=p1&limit=5",
            headers={"Authorization": "Bearer x"},
        )
    assert response.status_code == 200
    [listed] = response.json()
    assert listed["id"] == "a1"
    assert listed["action"] == "update"  # the entry's fields, flat beside its id
    assert listed["at"].startswith("2026-01-03")
    fake.list_entries.assert_called_once_with(collection="projects", doc_id="p1", limit=5)
