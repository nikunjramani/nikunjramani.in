"""Firebase Functions entrypoint — the one module the Firebase CLI and functions_framework load.

Each main domain's `src/<domain>/main.py` lists the functions it deploys and the subdomain
`main` module that defines each one; this file merges those tables. Every Firebase function
is defined in its subdomain's own `main.py` (ADR 0017).

FUNCTION_TARGET: inside a deployed function's container it names exactly that function, so
only its subdomain module is imported — one function's cold start never builds another's
FastAPI app. Unset (deploy discovery, the emulator, pytest), everything is imported.
"""

from __future__ import annotations

import importlib
import os

from firebase_functions.options import set_global_options

from kernel.config import get_settings
from src.content.main import FUNCTIONS as CONTENT
from src.identity.main import FUNCTIONS as IDENTITY
from src.inbox.main import FUNCTIONS as INBOX
from src.media.main import FUNCTIONS as MEDIA
from src.ops.main import FUNCTIONS as OPS

# Apply before any decorator runs, triggers and the scheduled backup included.
set_global_options(service_account=get_settings().runtime_service_account, max_instances=3)

FUNCTIONS: dict[str, str] = {**CONTENT, **IDENTITY, **INBOX, **MEDIA, **OPS}

_target = os.environ.get("FUNCTION_TARGET")
for _name, _module in FUNCTIONS.items():
    if _target is None or _target == _name:
        globals()[_name] = getattr(importlib.import_module(_module), _name)

__all__ = sorted(FUNCTIONS)
