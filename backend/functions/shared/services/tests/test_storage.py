"""StorageService, with the actual GCS/IAM calls mocked — signed URL generation cannot be
exercised for real outside a deployed environment. See the module docstring in
shared/services/storage.py for why."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from shared.core.errors import ValidationError
from shared.services.storage import (
    ALLOWED_CONTENT_TYPES,
    MAX_UPLOAD_BYTES,
    StorageService,
    new_object_path,
    validate_upload,
)

# ── validate_upload ──────────────────────────────────────────────────


def test_validate_upload_accepts_every_allowed_type() -> None:
    for content_type in ALLOWED_CONTENT_TYPES:
        validate_upload(content_type, 1024)  # must not raise


def test_validate_upload_rejects_an_unsupported_type() -> None:
    with pytest.raises(ValidationError):
        validate_upload("application/pdf", 1024)


def test_validate_upload_rejects_zero_bytes() -> None:
    with pytest.raises(ValidationError):
        validate_upload("image/webp", 0)


def test_validate_upload_rejects_oversized_files() -> None:
    with pytest.raises(ValidationError):
        validate_upload("image/webp", MAX_UPLOAD_BYTES + 1)


def test_validate_upload_accepts_the_exact_limit() -> None:
    validate_upload("image/webp", MAX_UPLOAD_BYTES)


# ── new_object_path ──────────────────────────────────────────────────


def test_object_path_uses_the_right_extension_and_lives_under_public() -> None:
    path = new_object_path("image/png")
    assert path.startswith("public/media/")
    assert path.endswith("/original.png")


def test_object_path_is_unique_per_call() -> None:
    assert new_object_path("image/webp") != new_object_path("image/webp")


# ── signed URL generation ────────────────────────────────────────────


def test_signed_url_uses_the_deployed_service_account_when_available() -> None:
    """On a real deployed function, ambient credentials carry a service_account_email —
    that's what triggers IAM signBlob-based signing instead of needing a private key."""
    fake_creds = MagicMock(service_account_email="runtime@project.iam.gserviceaccount.com")
    fake_creds.token = "fake-access-token"
    fake_blob = MagicMock()
    fake_blob.generate_signed_url.return_value = "https://signed.example.com/upload"

    client = MagicMock()
    client.bucket.return_value.blob.return_value = fake_blob
    svc = StorageService(client)

    with patch("shared.services.storage.google.auth.default", return_value=(fake_creds, "proj")):
        url = svc.create_signed_upload_url(
            path="public/media/x/original.webp", content_type="image/webp"
        )

    assert url == "https://signed.example.com/upload"
    fake_creds.refresh.assert_called_once()
    _, kwargs = fake_blob.generate_signed_url.call_args
    assert kwargs["service_account_email"] == "runtime@project.iam.gserviceaccount.com"
    assert kwargs["access_token"] == "fake-access-token"
    assert kwargs["method"] == "PUT"


def test_signed_url_falls_back_without_service_account_email() -> None:
    """Local `gcloud auth application-default login` user credentials have no
    service_account_email — signing then falls back to whatever generate_signed_url does
    by default (which will fail without a private key, but that failure belongs to the
    real call, not to this code silently mis-signing something)."""
    fake_creds = MagicMock(spec=["refresh", "token"])
    fake_creds.token = "unused"
    del fake_creds.service_account_email  # MagicMock(spec=...) would otherwise fake this too
    fake_blob = MagicMock()
    fake_blob.generate_signed_url.return_value = "https://signed.example.com/upload"

    client = MagicMock()
    client.bucket.return_value.blob.return_value = fake_blob
    svc = StorageService(client)

    with patch("shared.services.storage.google.auth.default", return_value=(fake_creds, "proj")):
        svc.create_signed_upload_url(path="p", content_type="image/webp")

    _, kwargs = fake_blob.generate_signed_url.call_args
    assert "service_account_email" not in kwargs
    assert "access_token" not in kwargs


def test_public_url_points_at_the_configured_bucket() -> None:
    svc = StorageService(MagicMock())
    assert svc.public_url("public/media/x/original.webp").startswith(
        "https://storage.googleapis.com/nikunjramani-in-media/"
    )


def test_delete_targets_the_right_blob() -> None:
    client = MagicMock()
    svc = StorageService(client)
    svc.delete("public/media/x/original.webp")
    client.bucket.return_value.blob.assert_called_with("public/media/x/original.webp")
    client.bucket.return_value.blob.return_value.delete.assert_called_once()
