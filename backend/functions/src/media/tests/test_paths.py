from __future__ import annotations

import pytest

from src.media.paths import (
    UPLOAD_PATTERN,
    asset_id_of,
    new_upload_path,
    processed_path,
    thumbnail_path,
)


def test_uploads_land_outside_the_public_folder() -> None:
    path = new_upload_path("png")
    assert path.startswith("uploads/media/")
    assert path.endswith("/original.png")
    assert UPLOAD_PATTERN.match(path)


def test_upload_paths_are_unique() -> None:
    assert new_upload_path("webp") != new_upload_path("webp")


def test_derivatives_are_public_and_never_match_the_upload_pattern() -> None:
    for path in (processed_path("abc"), thumbnail_path("abc")):
        assert path.startswith("public/media/abc/")
        assert not UPLOAD_PATTERN.match(path)


@pytest.mark.parametrize(
    "path",
    ["uploads/media/abc123/original.jpg", "public/media/abc123/original.jpg"],
    ids=["current-layout", "legacy-public-original"],
)
def test_asset_id_is_read_from_either_layout(path: str) -> None:
    assert asset_id_of(path) == "abc123"


def test_asset_id_rejects_a_foreign_path() -> None:
    with pytest.raises(ValueError):
        asset_id_of("backups/2026/skills.json")
