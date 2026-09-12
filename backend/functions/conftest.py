"""Fixtures shared across integration tests that hit the Firestore emulator.

Requires `firebase emulators:start --only firestore` running separately — these are
integration tests, not unit tests. Any test that requests `db` (directly, or via
`clean_collection`, which depends on it) skips automatically when the emulator is not
reachable, so `make test` still works offline with no marker needed in the test file
itself. Lives at the project root, not under shared/, so every domain's tests can use it
— pytest only shares a conftest's fixtures within its own directory subtree.
"""

from __future__ import annotations

import os
import socket
from collections.abc import Iterator

import pytest
from google.cloud.firestore_v1 import Client

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "nikunjramani-in")


def _emulator_reachable() -> bool:
    host, _, port = os.environ["FIRESTORE_EMULATOR_HOST"].partition(":")
    try:
        with socket.create_connection((host, int(port)), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.fixture
def db() -> Client:
    if not _emulator_reachable():
        pytest.skip("Firestore emulator not reachable on FIRESTORE_EMULATOR_HOST")
    from shared.core.firebase import get_db

    return get_db()


@pytest.fixture
def clean_collection(db: Client) -> Iterator[str]:
    """Yields a scratch collection name and wipes it afterwards."""
    name = "_test_scratch"
    yield name
    for doc in db.collection(name).stream():
        doc.reference.delete()
