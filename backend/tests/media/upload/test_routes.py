from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from kernel.app import make_app
from src.media.upload.routes import get_upload_service, router

ADMIN = {"uid": "admin-1", "admin": True}


def _client(fake: MagicMock) -> TestClient:
    app = make_app(router, "upload-test")
    app.dependency_overrides[get_upload_service] = lambda: fake
    return TestClient(app)


def test_upload_url_requires_admin() -> None:
    response = _client(MagicMock()).post("/", json={"contentType": "image/webp", "sizeBytes": 1})
    assert response.status_code == 401


def test_upload_url_returns_camel_case_wire_format() -> None:
    fake = MagicMock()
    fake.request_upload.return_value = {
        "uploadUrl": "https://x",
        "path": "uploads/media/1/original.webp",
    }
    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        response = _client(fake).post(
            "/",
            json={"contentType": "image/webp", "sizeBytes": 1},
            headers={"Authorization": "Bearer x"},
        )
    assert response.status_code == 200
    assert response.json() == {"uploadUrl": "https://x", "path": "uploads/media/1/original.webp"}
