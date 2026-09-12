"""Firebase Functions entrypoint.

Every deployed function is imported and re-exported here — this file is what
functions_framework loads to find them. That loading is unconditional: at runtime it
execs this entire module before plucking out the one target function it actually needs
(see functions_framework._function_registry.load_user_function, and
firebase_functions.private.serving.get_functions for the equivalent used by `firebase
deploy`'s manifest discovery). A flat `from src.X import api_X` for every domain would
therefore import — and fully construct the FastAPI app for — every OTHER domain on every
single cold start, regardless of which one is actually serving the request. That defeats
the entire reason for splitting into one function per domain (ADR 0011).

FUNCTION_TARGET is the fix: it is set to exactly one function's name inside a deployed
function's own container, and unset everywhere imports need to see everything at once —
the emulator, pytest, and the CLI's own manifest-discovery step. So: import everything
when it's unset, and only the matching domain when it's set.

⚠️ Adding a domain means adding its line here too, or FUNCTION_TARGET-based deploys will
silently 404 for it even though `next.config.ts` and the importlinter contract are both
updated correctly.
"""

from __future__ import annotations

import os

_target = os.environ.get("FUNCTION_TARGET")


def _wanted(name: str) -> bool:
    return _target is None or _target == name


if _wanted("api_system"):
    from src.system import api_system

if _wanted("api_contact"):
    from src.contact import api_contact

__all__ = ["api_contact", "api_system"]
