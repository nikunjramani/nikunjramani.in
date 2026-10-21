"""POST /internal/jobs/backup runs the export — what Cloud Scheduler calls daily."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from kernel.app import make_app
from src.ops.backup.events import router


def test_the_job_runs_the_export() -> None:
    service = MagicMock()
    with patch("src.ops.backup.events.BackupService", return_value=service):
        response = TestClient(make_app(router, "backup")).post("/backup")
    assert response.status_code == 204
    service.export_all.assert_called_once_with()
