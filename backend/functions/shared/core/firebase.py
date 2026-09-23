"""Firebase Admin SDK initialisation.

Uses ambient credentials — the runtime service account in production, the emulator locally.
No key file is ever read, which is why none exists in this repo.
"""

from typing import cast

import firebase_admin
from firebase_admin import firestore
from google.cloud.firestore import Client


def ensure_app() -> firebase_admin.App:
    """Idempotent: returns the existing default app, or creates it on first call.

    Not just get_db()'s implementation detail — shared/core/security.py calls this too.
    `require_admin` verifies the caller's token before any route body runs, so on a cold
    Cloud Functions instance it is the *first* Admin SDK call of the request, often before
    anything else has had a chance to call get_db() and create the app as a side effect.
    Without an explicit call here, that first verify_id_token() fails with "the default
    Firebase app does not exist" — caught by security.py's broad except and reported as
    "Invalid or expired token", which is a confusing way to fail and, on some deployments,
    fails forever (nothing else ever gets a chance to create the app if auth always fails
    first). Every unit test mocks verify_id_token directly, so nothing here ever exercised
    the real code path — only caught by testing against the actual Functions emulator.
    """
    try:
        return firebase_admin.get_app()
    except ValueError:
        return firebase_admin.initialize_app()


def get_db() -> Client:
    """Firestore client. The only place the SDK is constructed."""
    return cast("Client", firestore.client(ensure_app()))
