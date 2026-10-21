"""POST /internal/events/media-uploaded hands the finalized object to the service — the
HTTP successor of the old Storage-trigger function (InternalCaller: tests/kernel/test_events.py)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from kernel.app import make_app
from src.media.processing.events import router


def test_the_uploaded_object_reaches_the_service() -> None:
    service = MagicMock()
    with patch("src.media.processing.events.ProcessingService", return_value=service):
        response = TestClient(make_app(router, "processing")).post(
            "/media-uploaded",
            json={
                "bucket": "nikunjramani-in-media",
                "name": "uploads/media/x/original.jpg",
                "metadata": {"uploadedBy": "u1"},
            },
        )
    assert response.status_code == 204
    service.handle_upload.assert_called_once_with("uploads/media/x/original.jpg", uploaded_by="u1")


def test_an_object_without_metadata_is_still_handled() -> None:
    service = MagicMock()
    with patch("src.media.processing.events.ProcessingService", return_value=service):
        TestClient(make_app(router, "processing")).post(
            "/media-uploaded", json={"bucket": "b", "name": "public/media/x/processed.webp"}
        )
    service.handle_upload.assert_called_once_with("public/media/x/processed.webp", uploaded_by=None)
