"""ISO string <-> Firestore Timestamp conversion.

Schemas store dates as ISO 8601 strings (JSON has no native date type). Firestore stores
its own Timestamp type. This is the *only* place that boundary is crossed — repositories
call these on the way in and out, and nothing else needs to know Firestore's type exists.
"""

import re
from datetime import UTC, datetime
from typing import Any


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def to_firestore(data: dict[str, Any]) -> dict[str, Any]:
    """Convert ISO datetime strings to native datetimes before a write.

    The Firestore client accepts Python datetimes directly and stores them as its native
    Timestamp type — no explicit Timestamp construction needed.
    """
    result = _walk(data, _iso_to_datetime)
    assert isinstance(result, dict)
    return result


def from_firestore(data: dict[str, Any]) -> dict[str, Any]:
    """Convert a document's Timestamp fields back to ISO strings.

    Note: this does NOT attach the document id — the generated schemas have no `id`
    field (additionalProperties is false), so the id is carried alongside the model in
    shared.repositories.base.Record instead.
    """
    result = _walk(data, _datetime_to_iso)
    assert isinstance(result, dict)
    return result


# Only a full date-time ("2026-01-05T10:00:00Z") is treated as a timestamp. Anything looser
# is ambiguous: the slug "20210601" and the ISO week "2021-W01" both parse as dates, so a
# looser rule silently corrupts perfectly valid content. Schema fields that are dates use
# format: date-time, which always serialises with a time part.
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")


def _iso_to_datetime(value: Any) -> Any:
    if isinstance(value, str) and _DATETIME_RE.match(value):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return value
    return value


def _datetime_to_iso(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _walk(data: Any, fn: Any) -> Any:
    if isinstance(data, dict):
        return {k: _walk(v, fn) for k, v in data.items()}
    if isinstance(data, list):
        return [_walk(v, fn) for v in data]
    return fn(data)
