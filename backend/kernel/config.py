"""Settings the whole service needs. Domain-specific settings (buckets, API keys, addresses)
live in that domain's own settings module, so the kernel knows no domain."""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Cloud Run gets GOOGLE_CLOUD_PROJECT from backend/deploy/<project>.yaml; FIREBASE_PROJECT_ID
    # wins locally (.env).
    firebase_project_id: str = Field(
        default="nikunjramani-in",
        validation_alias=AliasChoices("FIREBASE_PROJECT_ID", "GOOGLE_CLOUD_PROJECT"),
    )
    environment: Literal["development", "production"] = "development"
    allowed_origins: str = "http://localhost:3000"
    # This service's own URLs, comma-separated (Cloud Run serves one service at more than one):
    # the audiences Eventarc and Cloud Scheduler may sign their tokens for (kernel/events.py).
    # Empty locally, where /internal/* accepts unsigned calls.
    service_url: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def service_audiences(self) -> list[str]:
        return [u.strip() for u in self.service_url.split(",") if u.strip()]

    @property
    def runtime_service_account(self) -> str:
        """Created by infra/terraform/modules/iam. The service runs as it, and Eventarc and
        Cloud Scheduler sign their calls to /internal/* as it — the name predates Cloud Run."""
        return f"functions-runtime@{self.firebase_project_id}.iam.gserviceaccount.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
