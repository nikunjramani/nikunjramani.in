"""Auth.

Signing in with Google is not enough. Authorisation is the `admin: true` custom claim,
which can only be set server-side — see infra/scripts/set_admin_claim.py.

`require_admin` is the FastAPI dependency every admin route in every domain carries. It
is built and tested once here, against a throwaway route in this module's own test file,
rather than proven for the first time against whichever content domain happens to be
built first.

It hands routes an `Actor`, not the token's claims: services need to know *who* acted (for
the audit trail and a few rules), never how Firebase spells it in a token.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header
from firebase_admin import auth

from kernel.errors import PermissionDeniedError
from kernel.firebase import ensure_app


class AuthError(PermissionDeniedError):
    status_code = 401
    code = "unauthenticated"


@dataclass(frozen=True, slots=True)
class Actor:
    """The verified admin behind a request — what an audit entry records as its actor."""

    uid: str
    email: str | None = None


def verify_token(authorization: str | None) -> dict[str, object]:
    """Verify a Bearer ID token. Raises AuthError if absent or invalid.

    ensure_app() first: this runs before any route body, so on a cold instance it is
    typically the first Admin SDK call of the whole request — nothing has necessarily
    called get_db() yet to create the app as a side effect. Without this, verify_id_token
    raises "the default Firebase app does not exist", indistinguishable from a bad token
    once the broad except below wraps it. See kernel/firebase.py's ensure_app docstring.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("Missing bearer token.")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        ensure_app()
        return dict(auth.verify_id_token(token))
    except Exception as exc:  # any verification failure is a 401, whatever the cause
        raise AuthError("Invalid or expired token.") from exc


def require_admin_claims(claims: dict[str, object]) -> Actor:
    """A valid token is 401-clearing. The claim is what actually authorises."""
    if claims.get("admin") is not True:
        raise PermissionDeniedError("Admin privileges required.")
    email = claims.get("email")
    return Actor(uid=str(claims["uid"]), email=email if isinstance(email, str) else None)


def require_admin(authorization: Annotated[str | None, Header()] = None) -> Actor:
    """`Depends(require_admin)` on every admin route, no exceptions — ADR 0011.

    A plain `def`, so FastAPI runs it in the threadpool: verifying a token can fetch
    Google's signing keys over the network, and an `async def` would stall every other
    request on the instance while it waits.
    """
    return require_admin_claims(verify_token(authorization))


Admin = Annotated[Actor, Depends(require_admin)]
