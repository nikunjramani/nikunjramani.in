"""Upload rules, and that a signed URL is only ever issued for a private uploads/ path."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from kernel.errors import ValidationError
from src.media.upload.service import (
    ALLOWED_CONTENT_TYPES,
    MAX_UPLOAD_BYTES,
    UploadService,
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


# ── signed upload ────────────────────────────────────────────────────


def test_request_upload_rejects_bad_content_type() -> None:
    storage = MagicMock()
    with pytest.raises(ValidationError):
        UploadService(storage=storage).request_upload(content_type="application/pdf", size_bytes=1)
    storage.create_signed_upload_url.assert_not_called()


def test_request_upload_signs_a_private_path() -> None:
    storage = MagicMock()
    storage.create_signed_upload_url.return_value = "https://signed.example.com/x"
    result = UploadService(storage=storage).request_upload(content_type="image/png", size_bytes=10)
    assert result["uploadUrl"] == "https://signed.example.com/x"
    assert result["path"].startswith("uploads/media/")  # private until processed
    assert result["path"].endswith("/original.png")
