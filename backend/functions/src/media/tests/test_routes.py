from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from shared.api import make_app
from shared.generated import MediaAsset
from shared.repositories.base import Record
from src.media.routes import get_media_service, router

ADMIN = {"uid": "admin-1", "admin": True}


def _client(fake_service: MagicMock) -> TestClient:
    app = make_app(router, "media-test")
    app.dependency_overrides[get_media_service] = lambda: fake_service
    return TestClient(app)


def test_upload_url_requires_admin() -> None:
    response = _client(MagicMock()).post(
        "/upload-url", json={"contentType": "image/webp", "sizeBytes": 1}
    )
    assert response.status_code == 401


def test_upload_url_returns_camel_case_wire_format() -> None:
    fake = MagicMock()
    fake.request_upload.return_value = {
        "uploadUrl": "https://x",
        "path": "public/media/1/original.webp",
    }
    with patch("shared.core.security.auth.verify_id_token", return_value=ADMIN):
        response = _client(fake).post(
            "/upload-url",
            json={"contentType": "image/webp", "sizeBytes": 1},
            headers={"Authorization": "Bearer x"},
        )
    assert response.status_code == 200
    assert response.json() == {"uploadUrl": "https://x", "path": "public/media/1/original.webp"}


def test_list_requires_admin() -> None:
    assert _client(MagicMock()).get("/").status_code == 401


def test_delete_requires_admin() -> None:
    assert _client(MagicMock()).delete("/some-id").status_code == 401


def test_update_metadata_requires_admin() -> None:
    response = _client(MagicMock()).patch("/some-id", json={"alt": "A photo"})
    assert response.status_code == 401


def test_update_metadata_returns_the_updated_record() -> None:
    fake = MagicMock()
    asset = MediaAsset.model_validate(
        {"url": "https://x", "path": "p", "uploadedAt": "2025-01-01T00:00:00Z", "alt": "A photo"}
    )
    fake.update_metadata.return_value = Record(id="some-id", data=asset)
    with patch("shared.core.security.auth.verify_id_token", return_value=ADMIN):
        response = _client(fake).patch(
            "/some-id",
            json={"alt": "A photo"},
            headers={"Authorization": "Bearer x"},
        )
    assert response.status_code == 200
    assert response.json()["data"]["alt"] == "A photo"
    fake.update_metadata.assert_called_once_with("some-id", alt="A photo", caption=None)
