"""Confirms /export.csv is matched as its own route, not swallowed by /{doc_id} —
registration order matters in FastAPI and is easy to get backwards by accident."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from shared.api import make_app
from shared.generated import ContactMessage
from shared.repositories.base import Record
from src.messages.routes import get_messages_service, router

ADMIN = {"uid": "admin-1", "admin": True}


def _client(fake_service: MagicMock) -> TestClient:
    app = make_app(router, "messages-test")
    app.dependency_overrides[get_messages_service] = lambda: fake_service
    return TestClient(app)


def test_list_requires_admin() -> None:
    assert _client(MagicMock()).get("/").status_code == 401


def test_export_route_is_not_shadowed_by_the_doc_id_route() -> None:
    fake = MagicMock()
    fake.export_csv.return_value = "name,email\nA,a@example.com\n"
    with patch("shared.core.security.auth.verify_id_token", return_value=ADMIN):
        response = _client(fake).get("/export.csv", headers={"Authorization": "Bearer x"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "A,a@example.com" in response.text
    fake.export_csv.assert_called_once()
    fake.get.assert_not_called()  # would have been hit if /{doc_id} swallowed the request


def test_mark_read_then_replied() -> None:
    fake = MagicMock()
    message = ContactMessage.model_validate(
        {"name": "A", "email": "a@example.com", "message": "hi", "read": True}
    )
    fake.mark_read.return_value = Record(id="m1", data=message)
    with patch("shared.core.security.auth.verify_id_token", return_value=ADMIN):
        response = _client(fake).patch("/m1/read", headers={"Authorization": "Bearer x"})
    assert response.status_code == 200
    assert response.json()["data"]["read"] is True
    fake.mark_read.assert_called_once_with("m1")
