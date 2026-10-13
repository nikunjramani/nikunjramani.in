from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class MediaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    storage_bucket: str = "nikunjramani-in-media"


@lru_cache
def get_media_settings() -> MediaSettings:
    return MediaSettings()
