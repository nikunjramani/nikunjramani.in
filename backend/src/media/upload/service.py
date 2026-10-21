"""Upload rules. The browser PUTs straight to Storage with the signed URL; nothing passes
through Python but the decision to allow it."""

from __future__ import annotations

from kernel.errors import ValidationError
from src.media.bucket import new_upload_path
from src.media.upload.storage import UploadStorage

ALLOWED_CONTENT_TYPES = {
    "image/webp": "webp",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MiB — a generous ceiling for source images


def validate_upload(content_type: str, size_bytes: int) -> None:
    if content_type not in ALLOWED_CONTENT_TYPES:
        allowed = ", ".join(sorted(ALLOWED_CONTENT_TYPES))
        raise ValidationError(f"Unsupported content type '{content_type}'. Allowed: {allowed}.")
    if size_bytes <= 0 or size_bytes > MAX_UPLOAD_BYTES:
        raise ValidationError(f"File size must be between 1 byte and {MAX_UPLOAD_BYTES} bytes.")


class UploadService:
    def __init__(self, storage: UploadStorage | None = None) -> None:
        self._storage = storage if storage is not None else UploadStorage()

    def request_upload(self, *, content_type: str, size_bytes: int) -> dict[str, str]:
        validate_upload(content_type, size_bytes)
        path = new_upload_path(ALLOWED_CONTENT_TYPES[content_type])
        upload_url = self._storage.create_signed_upload_url(path=path, content_type=content_type)
        return {"uploadUrl": upload_url, "path": path}
