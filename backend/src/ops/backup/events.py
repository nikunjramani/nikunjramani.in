"""ops/backup — HTTP entry point: Cloud Scheduler calls POST /internal/jobs/backup daily.

HTTP only: verify the caller, delegate. A plain `def`, so the export runs in the threadpool."""

from __future__ import annotations

from fastapi import APIRouter, Response

from kernel.events import InternalCaller
from src.ops.backup.service import BackupService

router = APIRouter(dependencies=[InternalCaller])


@router.post("/backup", status_code=204)
def backup() -> Response:
    BackupService().export_all()
    return Response(status_code=204)
