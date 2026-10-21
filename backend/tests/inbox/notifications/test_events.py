"""POST /internal/events/contact-created emails the new message — the HTTP successor of the
old Firestore-trigger function."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient
from google.events.cloud.firestore_v1.types import Document, DocumentEventData, Value

from kernel.app import make_app
from src.inbox.notifications.events import router


def test_the_new_message_is_passed_to_notify_owner() -> None:
    event = DocumentEventData(
        value=Document(
            name="projects/p/databases/(default)/documents/contact_messages/m1",
            fields={"name": Value(string_value="Ada"), "message": Value(string_value="Hi")},
        )
    )
    with patch("src.inbox.notifications.events.notify_owner") as notify:
        response = TestClient(make_app(router, "notifications")).post(
            "/contact-created",
            content=DocumentEventData.serialize(event),
            headers={"Content-Type": "application/protobuf"},
        )
    assert response.status_code == 204
    notify.assert_called_once_with({"name": "Ada", "message": "Hi"})


def test_a_failed_send_is_a_5xx_so_eventarc_retries() -> None:
    event = DocumentEventData(value=Document(name="projects/p/databases/(default)/documents/c/m"))
    with patch("src.inbox.notifications.events.notify_owner", side_effect=RuntimeError("smtp")):
        client = TestClient(make_app(router, "notifications"), raise_server_exceptions=False)
        response = client.post("/contact-created", content=DocumentEventData.serialize(event))
    assert response.status_code == 500
