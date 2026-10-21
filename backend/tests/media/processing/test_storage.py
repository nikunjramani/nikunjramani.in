from __future__ import annotations

from unittest.mock import MagicMock

from src.media.processing.storage import ProcessingStorage


def test_upload_and_download_use_the_media_bucket() -> None:
    client = MagicMock()
    storage = ProcessingStorage(client)
    storage.upload_bytes("public/media/x/t.webp", b"data", content_type="image/webp")
    client.bucket.assert_called_with("nikunjramani-in-media")
    client.bucket.return_value.blob.return_value.upload_from_string.assert_called_once_with(
        b"data", content_type="image/webp"
    )
