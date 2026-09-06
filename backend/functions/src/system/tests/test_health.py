from fastapi.testclient import TestClient

from shared.api import make_app
from src.system.routes import router


def test_health_returns_ok() -> None:
    client = TestClient(make_app(router, "system"))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_docs_disabled_in_production(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """A production /docs endpoint leaks the whole API surface."""
    from shared.core import config

    monkeypatch.setenv("ENVIRONMENT", "production")
    config.get_settings.cache_clear()
    client = TestClient(make_app(router, "system"))
    assert client.get("/docs").status_code == 404
    config.get_settings.cache_clear()
