"""Deletes an asset's objects from the media bucket."""

from __future__ import annotations

from google.cloud.storage import Client as StorageClient

from src.media.bucket import media_bucket


class LibraryStorage:
    def __init__(self, client: StorageClient | None = None) -> None:
        self._client = client

    def delete(self, path: str) -> None:
        media_bucket(self._client).blob(path).delete()
