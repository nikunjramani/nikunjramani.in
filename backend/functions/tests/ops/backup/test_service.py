"""The export logic with both sides faked — no emulator or bucket needed."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from src.ops.backup.service import BACKED_UP_COLLECTIONS, BackupService


def test_every_collection_is_written_as_its_own_json_file() -> None:
    repo = MagicMock()
    repo.dump.side_effect = lambda c: [{"id": f"{c}-1", "data": {"name": c}}]
    storage = MagicMock()

    counts = BackupService(repo=repo, storage=storage).export_all()

    assert counts == dict.fromkeys(BACKED_UP_COLLECTIONS, 1)
    written = {
        call.args[0].split("/")[1]: call.args[1] for call in storage.write_json.call_args_list
    }
    assert set(written) == {f"{c}.json" for c in BACKED_UP_COLLECTIONS}
    assert json.loads(written["skills.json"]) == [{"id": "skills-1", "data": {"name": "skills"}}]


def test_all_files_of_one_run_share_a_timestamp_folder() -> None:
    storage = MagicMock()
    BackupService(repo=MagicMock(dump=lambda c: []), storage=storage).export_all(("a", "b"))
    folders = {call.args[0].split("/")[0] for call in storage.write_json.call_args_list}
    assert len(folders) == 1


def test_an_empty_collection_still_produces_a_file() -> None:
    storage = MagicMock()
    counts = BackupService(repo=MagicMock(dump=lambda c: []), storage=storage).export_all(("x",))
    assert counts == {"x": 0}
    assert json.loads(storage.write_json.call_args.args[1]) == []
