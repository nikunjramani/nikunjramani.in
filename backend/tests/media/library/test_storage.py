from __future__ import annotations

from unittest.mock import MagicMock

from src.media.library.storage import LibraryStorage


def test_delete_targets_the_right_blob_in_the_media_bucket() -> None:
    client = MagicMock()
    LibraryStorage(client).delete("public/media/x/processed.webp")
    client.bucket.assert_called_with("nikunjramani-in-media")
    client.bucket.return_value.blob.assert_called_with("public/media/x/processed.webp")
    client.bucket.return_value.blob.return_value.delete.assert_called_once()
