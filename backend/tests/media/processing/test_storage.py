from __future__ import annotations

from unittest.mock import MagicMock

from src.media.processing.storage import ProcessingStorage


def test_public_url_points_at_the_configured_bucket() -> None:
    url = ProcessingStorage(MagicMock()).public_url("public/media/x/processed.webp")
    assert (
        url == "https://storage.googleapis.com/nikunjramani-in-media/public/media/x/processed.webp"
    )


def test_upload_and_download_use_the_media_bucket() -> None:
    client = MagicMock()
    storage = ProcessingStorage(client)
    storage.upload_bytes("public/media/x/t.webp", b"data", content_type="image/webp")
    client.bucket.assert_called_with("nikunjramani-in-media")
    client.bucket.return_value.blob.return_value.upload_from_string.assert_called_once_with(
        b"data", content_type="image/webp"
    )
