"""Image processing: WebP conversion, a thumbnail, and a blurhash placeholder.

Pure functions over bytes in, bytes/values out — no Storage or Firestore access here, so
this is fully unit-testable without any emulator or live bucket.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import blurhash
from PIL import Image

THUMBNAIL_MAX_DIMENSION = 400
WEBP_QUALITY = 82
# 4x3 blurhash components is the library's own suggested default: enough detail for a
# placeholder, small enough to store as a ~30-character string in Firestore.
BLURHASH_COMPONENTS = (4, 3)


@dataclass(frozen=True, slots=True)
class ProcessedImage:
    original_webp: bytes
    thumbnail_webp: bytes
    width: int
    height: int
    blurhash: str


def process_image(raw: bytes) -> ProcessedImage:
    """Decode `raw`, convert to WebP, generate a thumbnail and a blurhash.

    Raises PIL.UnidentifiedImageError on data that isn't a decodable image — the caller
    (the on_media_uploaded trigger) lets that propagate; a corrupt or non-image upload
    should not silently produce a broken asset.
    """
    with Image.open(BytesIO(raw)) as opened:
        decoded = opened.convert("RGB") if opened.mode not in ("RGB", "RGBA") else opened.copy()
        width, height = decoded.size

        original_webp = _to_webp(decoded)

        thumb = decoded.copy()
        thumb.thumbnail(
            (THUMBNAIL_MAX_DIMENSION, THUMBNAIL_MAX_DIMENSION), Image.Resampling.LANCZOS
        )
        thumbnail_webp = _to_webp(thumb)

        hash_source = decoded.copy()
        hash_source.thumbnail((100, 100), Image.Resampling.LANCZOS)  # a tiny sample is enough
        hash_str = blurhash.encode(hash_source, *BLURHASH_COMPONENTS)

    return ProcessedImage(
        original_webp=original_webp,
        thumbnail_webp=thumbnail_webp,
        width=width,
        height=height,
        blurhash=hash_str,
    )


def _to_webp(img: Image.Image) -> bytes:
    buffer = BytesIO()
    img.save(buffer, format="WEBP", quality=WEBP_QUALITY)
    return buffer.getvalue()
