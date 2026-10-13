"""Locating an asset's objects for deletion.

The media bucket's layout (also in backend/functions/README.md):

    uploads/media/<id>/original.<ext>   raw upload — private, may carry EXIF/GPS
    public/media/<id>/processed.webp    world-readable derivatives, no EXIF
    public/media/<id>/thumbnail.webp

<id> is also the media_assets document id.

Assets created before uploads moved to uploads/ have `path` = public/media/<id>/original.<ext>;
asset_id_of reads either layout.
"""


def asset_id_of(original_path: str) -> str:
    parts = original_path.split("/")
    if len(parts) != 4 or parts[1] != "media":
        raise ValueError(f"not a media object path: {original_path!r}")
    return parts[2]


def processed_path(asset_id: str) -> str:
    return f"public/media/{asset_id}/processed.webp"


def thumbnail_path(asset_id: str) -> str:
    return f"public/media/{asset_id}/thumbnail.webp"
