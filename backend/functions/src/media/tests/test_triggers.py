from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.media.triggers import on_media_uploaded

ASSET_ID = "0123456789abcdef0123456789abcdef"


def _event(name: str) -> SimpleNamespace:
    return SimpleNamespace(data=SimpleNamespace(name=name, metadata=None))


def _run(name: str, *, already_recorded: bool) -> tuple[MagicMock, MagicMock]:
    storage = MagicMock()
    storage.public_url.side_effect = lambda path: f"https://cdn/{path}"
    media = MagicMock()
    media.repo.exists.return_value = already_recorded
    processed = SimpleNamespace(
        original_webp=b"p", thumbnail_webp=b"t", width=10, height=5, blurhash="LKO2"
    )
    with (
        patch("src.media.triggers.StorageService", return_value=storage),
        patch("src.media.triggers.MediaService", return_value=media),
        patch("src.media.triggers.process_image", return_value=processed),
    ):
        on_media_uploaded.__wrapped__(_event(name))  # type: ignore[attr-defined]
    return storage, media


def test_own_output_is_ignored() -> None:
    storage, media = _run(f"public/media/{ASSET_ID}/processed.webp", already_recorded=False)
    storage.download_bytes.assert_not_called()
    media.create_from_processed_upload.assert_not_called()


def test_new_upload_is_processed_into_public_derivatives() -> None:
    storage, media = _run(f"uploads/media/{ASSET_ID}/original.jpg", already_recorded=False)
    written = [c.args[0] for c in storage.upload_bytes.call_args_list]
    assert written == [
        f"public/media/{ASSET_ID}/processed.webp",
        f"public/media/{ASSET_ID}/thumbnail.webp",
    ]
    kwargs = media.create_from_processed_upload.call_args.kwargs
    assert kwargs["asset_id"] == ASSET_ID
    assert kwargs["blurhash"] == "LKO2"


def test_redelivered_event_does_not_duplicate_the_asset() -> None:
    storage, media = _run(f"uploads/media/{ASSET_ID}/original.jpg", already_recorded=True)
    storage.download_bytes.assert_not_called()
    media.create_from_processed_upload.assert_not_called()
