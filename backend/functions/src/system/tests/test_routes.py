from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from shared.api import make_app
from src.system.routes import get_system_service, router


def test_resume_redirects_to_the_stored_url() -> None:
    fake = MagicMock()
    fake.get_resume_url.return_value = "https://storage.googleapis.com/x/resume.pdf"

    app = make_app(router, "system-test")
    app.dependency_overrides[get_system_service] = lambda: fake
    client = TestClient(app, follow_redirects=False)

    response = client.get("/resume")
    assert response.status_code == 302
    assert response.headers["location"] == "https://storage.googleapis.com/x/resume.pdf"
    fake.record_resume_download.assert_called_once()


def test_resume_is_a_real_404_when_none_uploaded() -> None:
    fake = MagicMock()
    from shared.core.errors import NotFoundError

    fake.get_resume_url.side_effect = NotFoundError("No resume has been uploaded yet.")

    app = make_app(router, "system-test")
    app.dependency_overrides[get_system_service] = lambda: fake
    client = TestClient(app)

    response = client.get("/resume")
    assert response.status_code == 404
