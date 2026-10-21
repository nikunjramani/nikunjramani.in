"""Signs upload URLs for the media bucket — the only way bytes enter it.

No key file: the runtime signs through IAM signBlob as its own service account
(google.auth.default() + refresh(), then service_account_email/access_token into
generate_signed_url). That only works for the deployed service's account, so it is
unit-tested with signing mocked and was verified live in Phase 6.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import google.auth
from google.auth.transport import requests as google_requests
from google.cloud.storage import Client as StorageClient

from src.media.bucket import media_bucket


class UploadStorage:
    def __init__(self, client: StorageClient | None = None) -> None:
        self._client = client

    def create_signed_upload_url(self, *, path: str, content_type: str) -> str:
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
            media_bucket(self._client)
            .blob(path)
            .generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=15),
                method="PUT",
                content_type=content_type,
                **signing_kwargs,
            )
        )
