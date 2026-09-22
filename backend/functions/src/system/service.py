"""Business logic for the system domain — kept out of routes.py per the router/service
split, even though this domain is small enough that it would be tempting to skip it."""

from __future__ import annotations

import contextlib
from typing import Any

from google.cloud.firestore_v1 import Client, CollectionReference, Increment, Query
from google.cloud.firestore_v1.base_query import FieldFilter

from shared.core.errors import NotFoundError
from shared.core.firebase import get_db
from shared.core.timestamps import from_firestore

_STATS_COLLECTION = "system_stats"
_RESUME_STATS_DOC = "resume"
_AUDIT_COLLECTION = "audit_log"


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

    def list_audit_log(
        self, *, collection: str | None = None, doc_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Every admin mutation writes an entry here (shared/services/audit.py) but nothing
        ever read it back until the admin panel's audit-trail UI needed to (Phase 5). The
        schema's own description says "never client-readable" — true of the Firestore rules
        (nothing reaches this collection except through an authenticated Python route, same
        as contact_messages or media_assets), not a ban on an admin ever seeing it here."""
        query: Query | CollectionReference = self._db.collection(_AUDIT_COLLECTION)
        if collection is not None:
            query = query.where(filter=FieldFilter("collection", "==", collection))
        if doc_id is not None:
            query = query.where(filter=FieldFilter("docId", "==", doc_id))
        query = query.order_by("at", direction=Query.DESCENDING).limit(limit)
        return [{"id": snap.id, **from_firestore(snap.to_dict() or {})} for snap in query.stream()]
