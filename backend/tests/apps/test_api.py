"""The assembled service: routes answer at /api/v1/<domain>/<sub> (with or without the
trailing slash the Next.js rewrite drops), and /internal/* is closed in production.
Which subdomains are mounted is tests/test_domain_registry.py's job."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from apps.api import create_app
from kernel import config


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(), follow_redirects=False)


@pytest.mark.parametrize("path", ["/api/v1/ops/health", "/api/v1/ops/health/"])
def test_health_answers_at_its_prefix(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_admin_routes_still_need_a_token(client: TestClient) -> None:
    assert client.get("/api/v1/content/projects").status_code == 401


@pytest.fixture
def production(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SERVICE_URL", "https://api-123.asia-south1.run.app")
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


@pytest.mark.parametrize(
    "path",
    [
        "/internal/events/media-uploaded",
        "/internal/events/contact-created",
        "/internal/jobs/backup",
    ],
)
def test_internal_routes_refuse_an_unsigned_call_in_production(production: None, path: str) -> None:
    client = TestClient(create_app())
    assert client.post(path).status_code == 401
