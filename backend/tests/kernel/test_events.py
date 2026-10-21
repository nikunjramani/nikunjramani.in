"""InternalCaller and the event readers, proven once here — every /internal/* route depends
on them. The token check mirrors tests/kernel/test_security.py for admins."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from fastapi import APIRouter, Request
from fastapi.testclient import TestClient
from google.events.cloud.firestore_v1.types import (
    ArrayValue,
    Document,
    DocumentEventData,
    MapValue,
    Value,
)
from google.protobuf.timestamp_pb2 import Timestamp

from kernel import config
from kernel.app import make_app
from kernel.events import InternalCaller, firestore_document, storage_object

SERVICE_URL = "https://api-123.asia-south1.run.app"
RUNTIME = "functions-runtime@nikunjramani-in.iam.gserviceaccount.com"

router = APIRouter(dependencies=[InternalCaller])


@router.post("/job")
async def job() -> dict[str, bool]:
    return {"ran": True}


@router.post("/storage")
async def storage(request: Request) -> dict[str, object]:
    obj = await storage_object(request)
    return {"name": obj.name, "metadata": obj.metadata}


@router.post("/firestore")
async def firestore(request: Request) -> dict[str, object]:
    doc_id, data = await firestore_document(request)
    return {"id": doc_id, "data": data}


@pytest.fixture
def production(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SERVICE_URL", SERVICE_URL)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "nikunjramani-in")
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def _client() -> TestClient:
    return TestClient(make_app(router, "events-test"))


def _post(path: str = "/job", token: str | None = "Bearer t") -> int:
    headers = {"Authorization": token} if token else {}
    response = _client().post(path, headers=headers)
    return int(response.status_code)


# ── who may call ─────────────────────────────────────────────────────


def test_no_token_in_production_is_401(production: None) -> None:
    assert _post(token=None) == 401


def test_invalid_token_is_401(production: None) -> None:
    with patch("kernel.events.id_token.verify_oauth2_token", side_effect=ValueError("bad")):
        assert _post() == 401


def test_the_audience_checked_is_this_service(production: None) -> None:
    with patch(
        "kernel.events.id_token.verify_oauth2_token",
        return_value={"email": RUNTIME, "email_verified": True},
    ) as verify:
        assert _post() == 200
    assert verify.call_args.kwargs["audience"] == [SERVICE_URL]


def test_another_account_is_403(production: None) -> None:
    with patch(
        "kernel.events.id_token.verify_oauth2_token",
        return_value={"email": "someone@example.com", "email_verified": True},
    ):
        assert _post() == 403


def test_an_unverified_email_is_403(production: None) -> None:
    with patch(
        "kernel.events.id_token.verify_oauth2_token",
        return_value={"email": RUNTIME, "email_verified": False},
    ):
        assert _post() == 403


def test_missing_service_url_refuses_rather_than_skipping_the_audience(
    production: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SERVICE_URL", "")
    config.get_settings.cache_clear()
    with patch("kernel.events.id_token.verify_oauth2_token") as verify:
        assert _post() == 403
    verify.assert_not_called()


def test_development_lets_an_unsigned_replay_through() -> None:
    assert _post(token=None) == 200


def test_development_still_verifies_a_token_that_is_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_URL", SERVICE_URL)
    config.get_settings.cache_clear()
    try:
        with patch("kernel.events.id_token.verify_oauth2_token", side_effect=ValueError("bad")):
            assert _post() == 401
    finally:
        config.get_settings.cache_clear()


# ── what arrives ─────────────────────────────────────────────────────


def test_storage_object_reads_name_and_metadata() -> None:
    body = {
        "bucket": "nikunjramani-in-media",
        "name": "uploads/media/a1/original.jpg",
        "metadata": {"uploadedBy": "u1"},
        "size": "123",
    }
    response = _client().post("/storage", json=body)
    assert response.json() == {
        "name": "uploads/media/a1/original.jpg",
        "metadata": {"uploadedBy": "u1"},
    }


def test_a_malformed_storage_event_is_422() -> None:
    assert _client().post("/storage", content=b"not json").status_code == 422


def test_firestore_document_decodes_every_value_kind() -> None:
    event = DocumentEventData(
        value=Document(
            name="projects/p/databases/(default)/documents/contact_messages/m1",
            fields={
                "name": Value(string_value="Ada"),
                "count": Value(integer_value=3),
                "spamScore": Value(double_value=0.25),
                "read": Value(boolean_value=False),
                "subject": Value(null_value=0),
                "createdAt": Value(timestamp_value=Timestamp(seconds=1_760_000_000)),
                "tags": Value(array_value=ArrayValue(values=[Value(string_value="x")])),
                "meta": Value(map_value=MapValue(fields={"ok": Value(boolean_value=True)})),
            },
        )
    )
    response = _client().post(
        "/firestore",
        content=DocumentEventData.serialize(event),
        headers={"Content-Type": "application/protobuf"},
    )
    assert response.json() == {
        "id": "m1",
        "data": {
            "name": "Ada",
            "count": 3,
            "spamScore": 0.25,
            "read": False,
            "subject": None,
            "createdAt": "2025-10-09T08:53:20+00:00",
            "tags": ["x"],
            "meta": {"ok": True},
        },
    }


def test_a_malformed_firestore_event_is_422() -> None:
    assert _client().post("/firestore", content=b"\xff\xff\xff").status_code == 422
