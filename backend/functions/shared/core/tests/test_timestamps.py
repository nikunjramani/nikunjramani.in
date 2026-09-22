from datetime import datetime

from shared.core.timestamps import from_firestore, to_firestore


def test_full_datetime_strings_become_datetimes() -> None:
    out = to_firestore({"at": "2026-01-05T10:00:00+00:00", "nested": {"t": "2026-01-05T10:00:00Z"}})
    assert isinstance(out["at"], datetime)
    assert isinstance(out["nested"]["t"], datetime)


def test_lookalike_strings_are_left_alone() -> None:
    """A numeric slug and a YYYY-MM date both look date-ish and must survive untouched."""
    data = {"slug": "20210601", "startDate": "2021-06", "week": "2021-W01", "day": "2025-01-05"}
    assert to_firestore(data) == data


def test_round_trip_through_from_firestore() -> None:
    written = to_firestore(
        {"at": "2026-01-05T10:00:00+00:00", "items": [{"t": "2026-01-05T10:00:00+00:00"}]}
    )
    back = from_firestore(written)
    assert back["at"].startswith("2026-01-05T10:00:00")
    assert back["items"][0]["t"].startswith("2026-01-05T10:00:00")
