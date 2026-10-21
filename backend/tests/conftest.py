"""Fixtures shared across integration tests that hit the Firestore emulator.

Requires `firebase emulators:start --only firestore` running separately — these are
integration tests, not unit tests. Any test that requests `db` (directly, or via
`clean_collection`, which depends on it) skips automatically when the emulator is not
reachable, so `make test` still works offline with no marker needed in the test file
itself. Lives at the root of tests/, so every domain's tests can use it.

The emulator needs no real Google credentials, so the Admin SDK is handed anonymous ones
here. Without that it hunts for Application Default Credentials (and the GCE metadata
server) on every client — slow, and a hard failure on a machine with no `gcloud` login.
"""

from __future__ import annotations

import os
import socket
from collections.abc import Iterator

import google.auth
import pytest
from google.auth.credentials import AnonymousCredentials, Credentials
from google.cloud.firestore_v1 import Client

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "nikunjramani-in")


def _emulator_credentials(*_args: object, **_kwargs: object) -> tuple[Credentials, str]:
    return AnonymousCredentials(), os.environ["GOOGLE_CLOUD_PROJECT"]  # type: ignore[no-untyped-call]


# Tests that exercise real credential handling (signed URLs) patch this themselves.
google.auth.default = _emulator_credentials


def _emulator_reachable() -> bool:
    host, _, port = os.environ["FIRESTORE_EMULATOR_HOST"].partition(":")
    try:
        with socket.create_connection((host, int(port)), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.fixture
def db() -> Iterator[Client]:
    if not _emulator_reachable():
        # CI sets this, so a broken emulator start fails the run instead of skipping every
        # emulator test.
        if os.environ.get("REQUIRE_FIRESTORE_EMULATOR"):
            pytest.fail("Firestore emulator not reachable on FIRESTORE_EMULATOR_HOST")
        pytest.skip("Firestore emulator not reachable on FIRESTORE_EMULATOR_HOST")
    from kernel.firebase import get_db

    client = get_db()
    _wipe(client, "audit_log")
    yield client
    _wipe(client, "audit_log")


def _wipe(db: Client, collection: str) -> None:
    for doc in db.collection(collection).stream():
        doc.reference.delete()


@pytest.fixture
def clean_collection(db: Client) -> Iterator[str]:
    """Yields a scratch collection name and wipes it afterwards."""
    name = "_test_scratch"
    yield name
    _wipe(db, name)
