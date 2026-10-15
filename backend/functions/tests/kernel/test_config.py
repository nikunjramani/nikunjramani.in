import pytest

from kernel.config import Settings


@pytest.fixture(autouse=True)
def _no_project_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)
    monkeypatch.delenv("GCLOUD_PROJECT", raising=False)


def test_deployed_project_comes_from_gcloud_project(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GCLOUD_PROJECT", "nikunjramani-in-staging")

    settings = Settings(_env_file=None)

    assert settings.firebase_project_id == "nikunjramani-in-staging"
    assert (
        settings.runtime_service_account
        == "functions-runtime@nikunjramani-in-staging.iam.gserviceaccount.com"
    )


def test_explicit_firebase_project_id_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "local-project")
    monkeypatch.setenv("GCLOUD_PROJECT", "nikunjramani-in-staging")

    assert Settings(_env_file=None).firebase_project_id == "local-project"


def test_defaults_to_prod_project_when_unset() -> None:
    assert Settings(_env_file=None).firebase_project_id == "nikunjramani-in"
