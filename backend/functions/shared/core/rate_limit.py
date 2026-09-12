"""Firestore-backed rate limiting: fixed-window, per-scope.

A transaction makes check-then-increment atomic, which matters — two concurrent requests
both reading count=4 against a limit of 5 must not both be allowed through. `Increment()`
alone cannot express "reject if this would exceed the limit", only "add N unconditionally".

Windows are identified by their start timestamp, so no separate cleanup step is needed to
begin a new window — but old window documents do accumulate. `_rate_limits` is on the TTL
policy in infra/terraform/modules/firestore alongside contact_messages, so Firestore
deletes them on its own schedule; nothing here depends on that for correctness.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from google.cloud.firestore_v1 import Client, Transaction, transactional

from shared.core.errors import RateLimitedError
from shared.core.firebase import get_db

_COLLECTION = "_rate_limits"


class RateLimiter:
    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    def check(self, *, scope: str, identifier: str, limit: int, window_seconds: int) -> None:
        """Raise RateLimitedError if `identifier` has hit `limit` requests in the current
        window for `scope`; otherwise record this request and return."""
        now = datetime.now(UTC)
        window_start = int(now.timestamp() // window_seconds) * window_seconds
        doc_id = f"{scope}_{identifier}_{window_start}".replace("/", "_")
        ref = self._db.collection(_COLLECTION).document(doc_id)

        transaction = self._db.transaction()
        _check_and_increment(transaction, ref, limit, now, window_seconds)


@transactional
def _check_and_increment(
    transaction: Transaction,
    ref: object,
    limit: int,
    now: datetime,
    window_seconds: int,
) -> None:
    snap = ref.get(transaction=transaction)  # type: ignore[attr-defined]
    count = int((snap.to_dict() or {}).get("count", 0)) if snap.exists else 0

    if count >= limit:
        raise RateLimitedError("Too many requests. Try again shortly.")

    transaction.set(
        ref,  # type: ignore[arg-type]
        {"count": count + 1, "expiresAt": now + timedelta(seconds=window_seconds * 2)},
    )
