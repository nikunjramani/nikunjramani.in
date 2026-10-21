from functools import lru_cache

from kernel.config import ServiceSettings


class BackupSettings(ServiceSettings):
    required_in_production = ("backups_bucket",)

    backups_bucket: str = "nikunjramani-in-backups"


@lru_cache
def get_backup_settings() -> BackupSettings:
    return BackupSettings()
