"""Business logic for the system domain — kept out of routes.py per the router/service
split, even though this domain is small enough that it would be tempting to skip it."""

from __future__ import annotations

import contextlib

from google.cloud.firestore_v1 import Client, Increment

from shared.core.errors import NotFoundError
from shared.core.firebase import get_db

_STATS_COLLECTION = "system_stats"
_RESUME_STATS_DOC = "resume"


class SystemService:
    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    def get_resume_url(self) -> str:
        snap = self._db.collection("profile").document("main").get()
        data = snap.to_dict() if snap.exists else None
        url = data.get("resumeUrl") if data else None
        if not url:
            raise NotFoundError("No resume has been uploaded yet.")
        return str(url)

    def record_resume_download(self) -> None:
        """Best-effort, atomic, and never blocks the redirect on failure — a visitor's
        download must succeed even if this bookkeeping write doesn't."""
        with contextlib.suppress(Exception):
            self._db.collection(_STATS_COLLECTION).document(_RESUME_STATS_DOC).set(
                {"downloadCount": Increment(1)}, merge=True
            )
