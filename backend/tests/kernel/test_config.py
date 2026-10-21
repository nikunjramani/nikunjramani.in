from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from kernel.config import ServiceSettings, Settings, get_settings


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Settings reads ./.env — run from an empty directory so a developer's .env can't leak in.
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("SERVICE_URL", raising=False)


def test_deployed_project_comes_from_google_cloud_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "nikunjramani-in-staging")

    settings = Settings()

    assert settings.firebase_project_id == "nikunjramani-in-staging"
    assert (
        settings.runtime_service_account
        == "functions-runtime@nikunjramani-in-staging.iam.gserviceaccount.com"
    )


def test_explicit_firebase_project_id_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "local-project")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "nikunjramani-in-staging")

    assert Settings().firebase_project_id == "local-project"


def test_defaults_to_prod_project_when_unset() -> None:
    assert Settings().firebase_project_id == "nikunjramani-in"


# ── production never falls back to a default (kernel/config.py) ─────────────


@pytest.fixture
def production(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("ENVIRONMENT", "production")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_production_refuses_the_default_project_and_an_empty_service_url(
    production: None,
) -> None:
    with pytest.raises(ValidationError, match="firebase_project_id, service_url"):
        Settings()


def test_production_starts_with_both_set(production: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "nikunjramani-in-staging")
    monkeypatch.setenv("SERVICE_URL", "https://api-1.asia-south1.run.app")
    assert Settings().firebase_project_id == "nikunjramani-in-staging"


def test_a_domain_setting_is_required_in_production_too(
    production: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "nikunjramani-in-staging")
    monkeypatch.setenv("SERVICE_URL", "https://api-1.asia-south1.run.app")

    class BucketSettings(ServiceSettings):
        required_in_production = ("bucket",)
        bucket: str = "prod-bucket"

    with pytest.raises(ValidationError, match="bucket"):
        BucketSettings()
    monkeypatch.setenv("BUCKET", "staging-bucket")
    assert BucketSettings().bucket == "staging-bucket"


def test_development_uses_the_defaults() -> None:
    class BucketSettings(ServiceSettings):
        required_in_production = ("bucket",)
        bucket: str = "prod-bucket"

    assert BucketSettings().bucket == "prod-bucket"
