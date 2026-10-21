from pathlib import Path

import pytest

from kernel.config import Settings


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Settings reads ./.env — run from an empty directory so a developer's .env can't leak in.
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)


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
