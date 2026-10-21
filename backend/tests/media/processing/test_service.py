from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PIL import UnidentifiedImageError

from src.media.processing.service import ProcessingService

ASSET_ID = "0123456789abcdef0123456789abcdef"


def _run(name: str, *, already_recorded: bool) -> tuple[MagicMock, MagicMock]:
    storage = MagicMock()
    repo = MagicMock()
    repo.exists.return_value = already_recorded
    processed = SimpleNamespace(
        original_webp=b"p", thumbnail_webp=b"t", width=10, height=5, blurhash="LKO2"
    )
    with patch("src.media.processing.service.process_image", return_value=processed):
        ProcessingService(repo=repo, storage=storage).handle_upload(name, uploaded_by=None)
    return storage, repo


def test_own_output_is_ignored() -> None:
    storage, repo = _run(f"public/media/{ASSET_ID}/processed.webp", already_recorded=False)
    storage.download_bytes.assert_not_called()
    repo.create.assert_not_called()


def test_new_upload_is_processed_into_public_derivatives() -> None:
    storage, repo = _run(f"uploads/media/{ASSET_ID}/original.jpg", already_recorded=False)
    written = [c.args[0] for c in storage.upload_bytes.call_args_list]
    assert written == [
        f"public/media/{ASSET_ID}/processed.webp",
        f"public/media/{ASSET_ID}/thumbnail.webp",
    ]
    asset_id, asset = repo.create.call_args.args
    assert asset_id == ASSET_ID
    assert asset.blurhash == "LKO2"
    assert asset.path == f"uploads/media/{ASSET_ID}/original.jpg"
    assert str(asset.url) == (
        f"https://storage.googleapis.com/nikunjramani-in-media/public/media/{ASSET_ID}/processed.webp"
    )


def test_redelivered_event_does_not_duplicate_the_asset() -> None:
    storage, repo = _run(f"uploads/media/{ASSET_ID}/original.jpg", already_recorded=True)
    storage.download_bytes.assert_not_called()
    repo.create.assert_not_called()


def test_a_file_that_is_not_an_image_is_logged_and_skipped_not_retried() -> None:
    storage = MagicMock()
    repo = MagicMock()
    repo.exists.return_value = False
    with patch(
        "src.media.processing.service.process_image",
        side_effect=UnidentifiedImageError("not an image"),
    ):
        result = ProcessingService(repo=repo, storage=storage).handle_upload(
            f"uploads/media/{ASSET_ID}/original.jpg", uploaded_by=None
        )
    assert result is None
    storage.upload_bytes.assert_not_called()
    repo.create.assert_not_called()
