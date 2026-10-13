"""Contact configuration. TURNSTILE_SECRET_KEY comes from Secret Manager (bound in main.py);
empty means "not configured", which only local development tolerates."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ContactSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    turnstile_secret_key: str = ""


@lru_cache
def get_contact_settings() -> ContactSettings:
    return ContactSettings()
