"""The media bucket layout, as each subdomain spells it out.

upload, processing and library each own the slice of the layout they use (no shared
paths module — ADR 0017). This is where those copies are held to one contract:
what upload writes is what processing picks up, and the derivatives processing writes are
exactly what library deletes.
"""

from __future__ import annotations

import pytest

from src.media.library import paths as library
from src.media.processing import paths as processing
from src.media.upload import paths as upload


def test_uploads_land_privately_and_are_picked_up_by_processing() -> None:
    path = upload.new_upload_path("png")
    assert path.startswith("uploads/media/")  # outside the public/ managed folder
    assert path.endswith("/original.png")
    match = processing.UPLOAD_PATTERN.match(path)
    assert match
    assert library.asset_id_of(path) == match.group("id")


def test_upload_paths_are_unique() -> None:
    assert upload.new_upload_path("webp") != upload.new_upload_path("webp")


def test_library_deletes_exactly_what_processing_writes() -> None:
    assert library.processed_path("abc") == processing.processed_path("abc")
    assert library.thumbnail_path("abc") == processing.thumbnail_path("abc")


def test_processing_never_reprocesses_its_own_output() -> None:
    for path in (processing.processed_path("a" * 32), processing.thumbnail_path("a" * 32)):
        assert path.startswith("public/media/")
        assert not processing.UPLOAD_PATTERN.match(path)


@pytest.mark.parametrize(
    "path",
    ["uploads/media/abc123/original.jpg", "public/media/abc123/original.jpg"],
    ids=["current-layout", "legacy-public-original"],
)
def test_library_reads_the_asset_id_from_either_layout(path: str) -> None:
    assert library.asset_id_of(path) == "abc123"


def test_library_rejects_a_foreign_path() -> None:
    with pytest.raises(ValueError):
        library.asset_id_of("backups/2026/skills.json")
