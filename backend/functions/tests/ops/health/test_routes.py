import pytest
from fastapi.testclient import TestClient

from kernel import config
from kernel.http import make_app
from src.ops.health.routes import router


def test_health_returns_ok() -> None:
    response = TestClient(make_app(router, "health")).get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_docs_disabled_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    """A production /docs endpoint leaks the whole API surface."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    config.get_settings.cache_clear()
    try:
        assert TestClient(make_app(router, "health")).get("/docs").status_code == 404
    finally:
        config.get_settings.cache_clear()
