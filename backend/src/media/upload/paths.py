"""Where uploads land.

The media bucket's layout (also in backend/README.md):

    uploads/media/<id>/original.<ext>   raw upload — private, may carry EXIF/GPS
    public/media/<id>/processed.webp    world-readable derivatives, no EXIF
    public/media/<id>/thumbnail.webp

<id> is also the media_assets document id.
"""

import uuid


def new_upload_path(extension: str) -> str:
    return f"uploads/media/{uuid.uuid4().hex}/original.{extension}"
