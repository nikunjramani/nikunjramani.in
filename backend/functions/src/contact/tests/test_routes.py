"""API-level tests: the request contract, not the business logic (that's test_service.py).

ContactService is swapped for a fake via FastAPI's dependency override — these tests
should not need a live Firestore emulator to confirm the route shape is right.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from shared.api import make_app
from src.contact.routes import get_contact_service, router


def _client(fake_service: MagicMock) -> TestClient:
    app = make_app(router, "contact")
    app.dependency_overrides[get_contact_service] = lambda: fake_service
    return TestClient(app)


def test_valid_submission_returns_generic_success() -> None:
    fake = MagicMock()
    response = _client(fake).post(
        "/contact",
        json={"name": "A Visitor", "email": "visitor@example.com", "message": "Hello!"},
    )
    assert response.status_code == 202
    assert response.json()["ok"] is True
    fake.submit.assert_called_once()


def test_honeypot_field_returns_the_same_success_shape() -> None:
    """A bot filling the honeypot must see an indistinguishable response — the whole
    point of the disguise is that probing the API can't reveal which check it hit."""
    fake = MagicMock()
    honest = _client(MagicMock()).post(
        "/contact",
        json={"name": "A", "email": "a@example.com", "message": "hi"},
    )
    tripped = _client(fake).post(
        "/contact",
        json={
            "name": "A",
            "email": "a@example.com",
            "message": "hi",
            "honeypot": "bot-filled-this",
        },
    )
    assert honest.status_code == tripped.status_code == 202
    assert honest.json() == tripped.json()


def test_missing_required_field_is_a_real_422() -> None:
    """Unlike anti-abuse failures, a genuine client error stays honest — the visitor
    benefits from being told what to fix."""
    response = _client(MagicMock()).post("/contact", json={"name": "A"})
    assert response.status_code == 422


def test_invalid_email_is_a_real_422() -> None:
    response = _client(MagicMock()).post(
        "/contact",
        json={"name": "A", "email": "not-an-email", "message": "hi"},
    )
    assert response.status_code == 422


def test_oversized_message_is_a_real_422() -> None:
    response = _client(MagicMock()).post(
        "/contact",
        json={"name": "A", "email": "a@example.com", "message": "x" * 5001},
    )
    assert response.status_code == 422


def test_client_ip_prefers_x_forwarded_for() -> None:
    fake = MagicMock()
    _client(fake).post(
        "/contact",
        json={"name": "A", "email": "a@example.com", "message": "hi"},
        headers={"x-forwarded-for": "9.9.9.9, 10.0.0.1"},
    )
    assert fake.submit.call_args.kwargs["ip"] == "9.9.9.9"


def test_docs_disabled_in_production() -> None:
    import os

    from shared.core import config

    old = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = "production"
    config.get_settings.cache_clear()
    try:
        client = TestClient(make_app(router, "contact"))
        assert client.get("/docs").status_code == 404
    finally:
        if old is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = old
        config.get_settings.cache_clear()
