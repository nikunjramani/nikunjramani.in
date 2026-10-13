from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.media.processing.main import on_media_uploaded


def test_trigger_hands_the_object_to_the_service() -> None:
    event = SimpleNamespace(
        data=SimpleNamespace(name="uploads/media/x/original.jpg", metadata={"uploadedBy": "u1"})
    )
    service = MagicMock()
    with patch("src.media.processing.main.ProcessingService", return_value=service):
        on_media_uploaded.__wrapped__(event)  # type: ignore[attr-defined]
    service.handle_upload.assert_called_once_with("uploads/media/x/original.jpg", uploaded_by="u1")
