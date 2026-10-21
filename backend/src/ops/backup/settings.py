from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BackupSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    backups_bucket: str = "nikunjramani-in-backups"


@lru_cache
def get_backup_settings() -> BackupSettings:
    return BackupSettings()
