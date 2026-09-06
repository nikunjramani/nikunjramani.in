"""Firebase Admin SDK initialisation.

Uses ambient credentials — the runtime service account in production, the emulator locally.
No key file is ever read, which is why none exists in this repo.
"""

from typing import cast

import firebase_admin
from firebase_admin import firestore
from google.cloud.firestore import Client


def _app() -> firebase_admin.App:
    try:
        return firebase_admin.get_app()
    except ValueError:
        return firebase_admin.initialize_app()


def get_db() -> Client:
    """Firestore client. The only place the SDK is constructed."""
    return cast("Client", firestore.client(_app()))
