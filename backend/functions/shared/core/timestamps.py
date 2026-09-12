"""ISO string <-> Firestore Timestamp conversion.

Schemas store dates as ISO 8601 strings (JSON has no native date type). Firestore stores
its own Timestamp type. This is the *only* place that boundary is crossed — repositories
call these on the way in and out, and nothing else needs to know Firestore's type exists.
"""

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


def _iso_to_datetime(value: Any) -> Any:
    # Heuristic: try to parse every string as a datetime, keep it as-is if that fails.
    # This model set has no field whose value coincidentally parses as ISO 8601 (a slug,
    # a URL, a name), so the false-positive rate is zero today. If that ever changes, the
    # right fix is deriving datetime field *paths* from the schema rather than sniffing
    # values — more machinery, not worth it while it stays unnecessary.
    if isinstance(value, str):
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
