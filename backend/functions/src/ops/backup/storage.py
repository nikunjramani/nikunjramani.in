"""Writes export files to the private backups bucket (30-day lifecycle, Terraform)."""

from __future__ import annotations

from google.cloud.storage import Client as StorageClient

from src.ops.backup.settings import get_backup_settings


class BackupStorage:
    def __init__(self, client: StorageClient | None = None) -> None:
        self._client = client if client is not None else StorageClient()

    def write_json(self, path: str, data: bytes) -> None:
        bucket = self._client.bucket(get_backup_settings().backups_bucket)
        bucket.blob(path).upload_from_string(data, content_type="application/json")
