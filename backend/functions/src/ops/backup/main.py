"""ops/backup — entry point: deploys nightly_backup (Cloud Scheduler, daily)."""

from firebase_functions import scheduler_fn

from src.ops.backup.service import BackupService


@scheduler_fn.on_schedule(schedule="every 24 hours", region="asia-south1", timeout_sec=300)
def nightly_backup(event: scheduler_fn.ScheduledEvent) -> None:
    BackupService().export_all()
