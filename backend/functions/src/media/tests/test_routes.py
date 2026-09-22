from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from shared.api import make_app
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
