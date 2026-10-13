"""UploadStorage with the GCS/IAM calls mocked — signed URL generation can't be exercised for
real outside a deployed environment (see src/media/upload/storage.py)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.media.upload.storage import UploadStorage


def test_signed_url_uses_the_deployed_service_account_when_available() -> None:
    """On a real deployed function, ambient credentials carry a service_account_email —
    that's what triggers IAM signBlob-based signing instead of needing a private key."""
    fake_creds = MagicMock(service_account_email="runtime@project.iam.gserviceaccount.com")
    fake_creds.token = "fake-access-token"
    fake_blob = MagicMock()
    fake_blob.generate_signed_url.return_value = "https://signed.example.com/upload"

    client = MagicMock()
    client.bucket.return_value.blob.return_value = fake_blob
    svc = UploadStorage(client)

    with patch("src.media.upload.storage.google.auth.default", return_value=(fake_creds, "proj")):
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
    svc = UploadStorage(client)

    with patch("src.media.upload.storage.google.auth.default", return_value=(fake_creds, "proj")):
        svc.create_signed_upload_url(path="p", content_type="image/webp")

    _, kwargs = fake_blob.generate_signed_url.call_args
    assert "service_account_email" not in kwargs
    assert "access_token" not in kwargs
