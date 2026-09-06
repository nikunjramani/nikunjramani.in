"""Firebase Functions entrypoint.

Every deployed function is imported and re-exported here. Keep this file thin — anything
imported at module level runs on every cold start of every function.

One function per domain: ADR 0011.
"""

from src.system import api_system

__all__ = ["api_system"]
