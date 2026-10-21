"""Deletes an asset's objects from the media bucket."""

from __future__ import annotations

from google.cloud.storage import Client as StorageClient

from src.media.library.settings import get_media_settings


class LibraryStorage:
    def __init__(self, client: StorageClient | None = None) -> None:
        self._client = client if client is not None else StorageClient()

    def delete(self, path: str) -> None:
        self._client.bucket(get_media_settings().storage_bucket).blob(path).delete()
