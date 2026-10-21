"""Reads raw uploads and writes the public derivatives, in the media bucket."""

from __future__ import annotations

from typing import Any

from google.cloud.storage import Client as StorageClient

from src.media.processing.settings import get_media_settings


class ProcessingStorage:
    def __init__(self, client: StorageClient | None = None) -> None:
        self._client = client if client is not None else StorageClient()

    @property
    def _bucket(self) -> Any:
        return self._client.bucket(get_media_settings().storage_bucket)

    def download_bytes(self, path: str) -> bytes:
        return bytes(self._bucket.blob(path).download_as_bytes())

    def upload_bytes(self, path: str, data: bytes, *, content_type: str) -> None:
        self._bucket.blob(path).upload_from_string(data, content_type=content_type)

    def public_url(self, path: str) -> str:
        return f"https://storage.googleapis.com/{get_media_settings().storage_bucket}/{path}"
