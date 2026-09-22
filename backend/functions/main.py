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

if _wanted("api_projects"):
    from src.projects import api_projects

if _wanted("api_skills"):
    from src.skills import api_skills

if _wanted("api_experience"):
    from src.experience import api_experience

if _wanted("api_education"):
    from src.education import api_education

if _wanted("api_certifications"):
    from src.certifications import api_certifications

if _wanted("api_posts"):
    from src.posts import api_posts

if _wanted("api_profile"):
    from src.profile import api_profile

if _wanted("api_settings"):
    from src.settings import api_settings

__all__ = [
    "api_certifications",
    "api_contact",
    "api_education",
    "api_experience",
    "api_posts",
    "api_profile",
    "api_projects",
    "api_settings",
    "api_skills",
    "api_system",
]
