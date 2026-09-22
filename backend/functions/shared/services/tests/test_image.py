from io import BytesIO

import pytest
from PIL import Image, UnidentifiedImageError

from shared.services.image import THUMBNAIL_MAX_DIMENSION, process_image


def _png_bytes(width: int, height: int, color: tuple[int, int, int] = (200, 50, 50)) -> bytes:
    buf = BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="PNG")
    return buf.getvalue()


def test_process_image_reports_original_dimensions() -> None:
    result = process_image(_png_bytes(1600, 900))
    assert (result.width, result.height) == (1600, 900)


def test_thumbnail_is_bounded_and_preserves_aspect_ratio() -> None:
    result = process_image(_png_bytes(2000, 1000))  # 2:1
    thumb = Image.open(BytesIO(result.thumbnail_webp))
    assert max(thumb.size) <= THUMBNAIL_MAX_DIMENSION
    assert abs(thumb.size[0] / thumb.size[1] - 2.0) < 0.05


def test_original_is_converted_to_webp() -> None:
    result = process_image(_png_bytes(400, 300))
    decoded = Image.open(BytesIO(result.original_webp))
    assert decoded.format == "WEBP"
    assert decoded.size == (400, 300)


def test_blurhash_is_a_non_empty_string() -> None:
    result = process_image(_png_bytes(400, 300))
    assert isinstance(result.blurhash, str)
    assert len(result.blurhash) > 10


def test_small_image_thumbnail_is_not_upscaled() -> None:
    """A 50x50 source has nothing to shrink to fit within 400px — the thumbnail should
    stay at the original size, not get blown up."""
    result = process_image(_png_bytes(50, 50))
    thumb = Image.open(BytesIO(result.thumbnail_webp))
    assert thumb.size == (50, 50)


def test_garbage_bytes_raise_rather_than_silently_produce_a_broken_asset() -> None:
    with pytest.raises(UnidentifiedImageError):
        process_image(b"this is not an image")
