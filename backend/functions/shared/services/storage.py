"""Firebase Storage access: signed upload URLs, and the object-path convention.

Signed URL generation cannot be exercised end to end outside a deployed environment. This
project deliberately never uses a service-account key file (ambient credentials only — see
shared/core/firebase.py), and signing a URL without a private key on disk requires calling
the IAM signBlob API on behalf of the *runtime* service account — google-auth's own
documented workaround for exactly this situation (google.auth.default() + credentials.
refresh() to get an access token, then pass service_account_email/access_token through to
generate_signed_url instead of a private key). That only works for a real deployed
function's service account: local `gcloud auth application-default login` user credentials
have no service_account_email at all. So this is unit-tested with the signing call mocked,
not exercised against a real bucket — Phase 6 needs one live signed-upload check once
billing is on.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

import google.auth
from google.auth.transport import requests as google_requests
from google.cloud.storage import Client as StorageClient

from shared.core.config import get_settings
from shared.core.errors import ValidationError

ALLOWED_CONTENT_TYPES = {
    "image/webp": "webp",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MiB — a generous ceiling for source images


def validate_upload(content_type: str, size_bytes: int) -> None:
    if content_type not in ALLOWED_CONTENT_TYPES:
        allowed = ", ".join(sorted(ALLOWED_CONTENT_TYPES))
        raise ValidationError(f"Unsupported content type '{content_type}'. Allowed: {allowed}.")
    if size_bytes <= 0 or size_bytes > MAX_UPLOAD_BYTES:
        raise ValidationError(f"File size must be between 1 byte and {MAX_UPLOAD_BYTES} bytes.")


def new_object_path(content_type: str) -> str:
    ext = ALLOWED_CONTENT_TYPES[content_type]
    return f"public/media/{uuid.uuid4().hex}/original.{ext}"


class StorageService:
    """Every method takes an optional `bucket` override — the media bucket
    (settings.storage_bucket) is the default, since that's what almost every caller wants,
    but nightly_backup writes to a separate bucket (settings.backups_bucket) with its own
    30-day lifecycle rule, and hardcoding one bucket name into every method would have
    silently sent backups into the public media bucket instead."""

    def __init__(self, client: StorageClient | None = None) -> None:
        self._client = client if client is not None else StorageClient()

    def create_signed_upload_url(
        self, *, path: str, content_type: str, bucket: str | None = None
    ) -> str:
        settings = get_settings()
        blob = self._client.bucket(bucket or settings.storage_bucket).blob(path)

        credentials, _project = google.auth.default()
        credentials.refresh(google_requests.Request())  # type: ignore[no-untyped-call]

        signing_kwargs: dict[str, Any] = {}
        service_account_email = getattr(credentials, "service_account_email", None)
        if service_account_email and service_account_email != "default":
            signing_kwargs = {
                "service_account_email": service_account_email,
                "access_token": credentials.token,
            }

        return str(
            blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=15),
                method="PUT",
                content_type=content_type,
                **signing_kwargs,
            )
        )

    def public_url(self, path: str, *, bucket: str | None = None) -> str:
        settings = get_settings()
        return f"https://storage.googleapis.com/{bucket or settings.storage_bucket}/{path}"

    def delete(self, path: str, *, bucket: str | None = None) -> None:
        settings = get_settings()
        self._client.bucket(bucket or settings.storage_bucket).blob(path).delete()

    def download_bytes(self, path: str, *, bucket: str | None = None) -> bytes:
        settings = get_settings()
        blob = self._client.bucket(bucket or settings.storage_bucket).blob(path)
        data = blob.download_as_bytes()
        return bytes(data)

    def upload_bytes(
        self, path: str, data: bytes, *, content_type: str, bucket: str | None = None
    ) -> None:
        settings = get_settings()
        blob = self._client.bucket(bucket or settings.storage_bucket).blob(path)
        blob.upload_from_string(data, content_type=content_type)
