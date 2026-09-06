"""Auth.

Signing in with Google is not enough. Authorisation is the `admin: true` custom claim,
which can only be set server-side — see infra/scripts/set_admin_claim.py.
"""

from firebase_admin import auth

from shared.core.errors import PermissionDeniedError


class AuthError(PermissionDeniedError):
    status_code = 401
    code = "unauthenticated"


def verify_token(authorization: str | None) -> dict[str, object]:
    """Verify a Bearer ID token. Raises AuthError if absent or invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("Missing bearer token.")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return dict(auth.verify_id_token(token))
    except Exception as exc:  # any verification failure is a 401, whatever the cause
        raise AuthError("Invalid or expired token.") from exc


def require_admin_claims(claims: dict[str, object]) -> dict[str, object]:
    """A valid token is 401-clearing. The claim is what actually authorises."""
    if claims.get("admin") is not True:
        raise PermissionDeniedError("Admin privileges required.")
    return claims
