"""src/media/bucket.py — the media bucket's name and layout, the one contract upload,
processing and library share (ADR 0024): what upload writes is what processing picks up,
and the derivatives processing writes are exactly what library deletes."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.media import bucket


def test_uploads_land_privately_and_are_new_work_for_processing() -> None:
    path = bucket.new_upload_path("png")
    assert path.startswith("uploads/media/")  # outside the public/ managed folder
    assert path.endswith("/original.png")
    match = bucket.UPLOAD_PATTERN.match(path)
    assert match
    assert bucket.asset_id_of(path) == match.group("id")


def test_upload_paths_are_unique() -> None:
    assert bucket.new_upload_path("webp") != bucket.new_upload_path("webp")


def test_derivatives_are_public_and_never_reprocessed() -> None:
    for path in (bucket.processed_path("a" * 32), bucket.thumbnail_path("a" * 32)):
        assert path.startswith("public/media/")
        assert not bucket.UPLOAD_PATTERN.match(path)


@pytest.mark.parametrize(
    "path",
    ["uploads/media/abc123/original.jpg", "public/media/abc123/original.jpg"],
    ids=["current-layout", "legacy-public-original"],
)
def test_the_asset_id_is_read_from_either_layout(path: str) -> None:
    assert bucket.asset_id_of(path) == "abc123"


def test_a_foreign_path_is_rejected() -> None:
    with pytest.raises(ValueError):
        bucket.asset_id_of("backups/2026/skills.json")


def test_public_url_points_at_the_configured_bucket() -> None:
    assert bucket.public_url("public/media/x/processed.webp") == (
        "https://storage.googleapis.com/nikunjramani-in-media/public/media/x/processed.webp"
    )


def test_media_bucket_uses_the_given_client_and_the_configured_name() -> None:
    client = MagicMock()
    assert bucket.media_bucket(client) is client.bucket.return_value
    client.bucket.assert_called_once_with("nikunjramani-in-media")
