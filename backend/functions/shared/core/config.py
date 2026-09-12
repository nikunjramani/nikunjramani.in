"""Environment-driven settings. Fails loudly at startup rather than mysteriously later."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    firebase_project_id: str = "nikunjramani-in"
    environment: Literal["development", "production"] = "development"

    # Secrets — empty locally, injected from Secret Manager in production.
    resend_api_key: str = ""
    contact_email_to: str = ""
    mail_from: str = "no-reply@nikunjramani.in"
    turnstile_secret_key: str = ""
    revalidate_token: str = ""

    allowed_origins: str = "http://localhost:3000"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
