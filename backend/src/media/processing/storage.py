"""Reads raw uploads and writes the public derivatives, in the media bucket."""

from __future__ import annotations

from google.cloud.storage import Client as StorageClient

from src.media.bucket import media_bucket


class ProcessingStorage:
    def __init__(self, client: StorageClient | None = None) -> None:
        self._client = client

    def download_bytes(self, path: str) -> bytes:
        return bytes(media_bucket(self._client).blob(path).download_as_bytes())

    def upload_bytes(self, path: str, data: bytes, *, content_type: str) -> None:
        media_bucket(self._client).blob(path).upload_from_string(data, content_type=content_type)
