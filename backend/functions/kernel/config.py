"""Settings every function needs. Domain-specific settings (buckets, API keys, addresses)
live in that domain's own settings module, so the kernel knows no domain."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    firebase_project_id: str = "nikunjramani-in"
    environment: Literal["development", "production"] = "development"
    allowed_origins: str = "http://localhost:3000"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def runtime_service_account(self) -> str:
        """Created by infra/terraform/modules/iam; every function runs as it."""
        return f"functions-runtime@{self.firebase_project_id}.iam.gserviceaccount.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
