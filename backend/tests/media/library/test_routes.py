from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from kernel.app import make_app
from kernel.records import Record
from kernel.security import Actor
from shared.generated import MediaAsset
from src.media.library.routes import get_library_service, router

ADMIN = {"uid": "admin-1", "admin": True}


def _client(fake_service: MagicMock) -> TestClient:
    app = make_app(router, "media-test")
    app.dependency_overrides[get_library_service] = lambda: fake_service
    return TestClient(app)


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
    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        response = _client(fake).patch(
            "/some-id",
            json={"alt": "A photo"},
            headers={"Authorization": "Bearer x"},
        )
    assert response.status_code == 200
    assert response.json()["data"]["alt"] == "A photo"
    fake.update_metadata.assert_called_once_with(
        "some-id", alt="A photo", caption=None, actor=Actor(uid="admin-1")
    )


def test_usage_requires_admin() -> None:
    assert _client(MagicMock()).get("/some-id/usage").status_code == 401


def test_usage_returns_the_references() -> None:
    fake = MagicMock()
    fake.usage.return_value = ["projects/stride"]
    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        response = _client(fake).get("/some-id/usage", headers={"Authorization": "Bearer x"})
    assert response.status_code == 200
    assert response.json() == {"references": ["projects/stride"]}


def test_delete_passes_force_through() -> None:
    fake = MagicMock()
    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        client = _client(fake)
        assert client.delete("/a1", headers={"Authorization": "Bearer x"}).status_code == 204
        fake.delete.assert_called_with("a1", Actor(uid="admin-1"), force=False)
        client.delete("/a1?force=true", headers={"Authorization": "Bearer x"})
        fake.delete.assert_called_with("a1", Actor(uid="admin-1"), force=True)
