"""Auth.

Signing in with Google is not enough. Authorisation is the `admin: true` custom claim,
which can only be set server-side — see infra/scripts/set_admin_claim.py.

`require_admin` is the FastAPI dependency every admin route in every domain carries. It
is built and tested once here, against a throwaway route in this module's own test file,
rather than proven for the first time against whichever content domain happens to be
built first.
"""

from typing import Annotated

from fastapi import Depends, Header
from firebase_admin import auth

from shared.core.errors import PermissionDeniedError
from shared.core.firebase import ensure_app


class AuthError(PermissionDeniedError):
    status_code = 401
    code = "unauthenticated"


def verify_token(authorization: str | None) -> dict[str, object]:
    """Verify a Bearer ID token. Raises AuthError if absent or invalid.

    ensure_app() first: this runs before any route body, so on a cold instance it is
    typically the first Admin SDK call of the whole request — nothing has necessarily
    called get_db() yet to create the app as a side effect. Without this, verify_id_token
    raises "the default Firebase app does not exist", indistinguishable from a bad token
    once the broad except below wraps it. See shared/core/firebase.py's ensure_app docstring.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("Missing bearer token.")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        ensure_app()
        return dict(auth.verify_id_token(token))
    except Exception as exc:  # any verification failure is a 401, whatever the cause
        raise AuthError("Invalid or expired token.") from exc


def require_admin_claims(claims: dict[str, object]) -> dict[str, object]:
    """A valid token is 401-clearing. The claim is what actually authorises."""
    if claims.get("admin") is not True:
        raise PermissionDeniedError("Admin privileges required.")
    return claims


async def require_admin(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    """`Depends(require_admin)` on every admin route, no exceptions — ADR 0011.

    Returns the verified claims (uid, email, admin, …) so a route can use them for the
    audit trail without verifying the token a second time.
    """
    return require_admin_claims(verify_token(authorization))


AdminClaims = Annotated[dict[str, object], Depends(require_admin)]
