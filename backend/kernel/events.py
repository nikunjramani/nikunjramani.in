"""Background work arriving over HTTP: who may call /internal/*, and how to read what arrives.

Eventarc (Storage and Firestore events) and Cloud Scheduler (the backup job) call routes under
/internal/* on the same public service as the API (ADR 0023). Cloud Run IAM can't protect a
path, so `InternalCaller` does: every call must carry a Google-signed ID token for one of
this service's URLs (SERVICE_URL), minted for this service's own runtime account — the
identity the triggers and the scheduler job are configured to sign as. Anything else is
401/403, like an admin route without the claim.

Locally (ENVIRONMENT=development) a call with no token is let through, so an event can be
replayed by hand against the emulators (RUNBOOK). A token that *is* sent is always verified.
"""

from __future__ import annotations

from datetime import UTC
from typing import Annotated, Any

from fastapi import Depends, Header, Request
from google.auth.transport import requests as google_requests
from google.events.cloud.firestore_v1.types import DocumentEventData
from google.oauth2 import id_token
from pydantic import BaseModel, Field

from kernel.config import get_settings
from kernel.errors import PermissionDeniedError, ValidationError
from kernel.security import AuthError


def verify_internal_caller(authorization: str | None, path: str) -> None:
    """`path` is the route the request arrived on. Cloud Scheduler signs for a service URL
    as given (modules/api); Eventarc signs for the service's `status.url` plus the trigger's
    destination path — so each configured URL is accepted bare and with this request's path."""
    settings = get_settings()
    if authorization is None and not settings.is_production:
        return  # local replay — see the module docstring
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("Missing bearer token.")
    if not settings.service_audiences:
        # Without an audience, any Google-signed token for this account would pass.
        raise PermissionDeniedError("SERVICE_URL is not configured.")
    try:
        claims = id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
            authorization.removeprefix("Bearer ").strip(),
            google_requests.Request(),
            audience=[a for url in settings.service_audiences for a in (url, f"{url}{path}")],
        )
    except Exception as exc:  # signature, expiry, issuer or audience — all a 401
        raise AuthError("Invalid or expired token.") from exc
    if claims.get("email") != settings.runtime_service_account or not claims.get("email_verified"):
        raise PermissionDeniedError("Not an internal caller.")


def require_internal_caller(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """`dependencies=[InternalCaller]` on every /internal/* router, no exceptions.

    A plain `def`, so FastAPI runs it in the threadpool: verification fetches Google's
    signing keys over the network, which must not stall the event loop."""
    verify_internal_caller(authorization, request.url.path)


InternalCaller = Depends(require_internal_caller)


# ── Cloud Storage: google.cloud.storage.object.v1.finalized (JSON) ──────────


class StorageObject(BaseModel):
    """The fields of Eventarc's StorageObjectData this service reads."""

    bucket: str
    name: str
    metadata: dict[str, str] = Field(default_factory=dict)


async def storage_object(request: Request) -> StorageObject:
    try:
        return StorageObject.model_validate_json(await request.body())
    except Exception as exc:
        raise ValidationError("Not a Cloud Storage object event.") from exc


# ── Firestore: google.cloud.firestore.document.v1.created (protobuf) ────────


async def firestore_document(request: Request) -> tuple[str, dict[str, Any]]:
    """(document id, data) of the document an event carries, as plain Python values —
    timestamps as ISO strings, the same shape kernel.timestamps.from_firestore produces."""
    try:
        event = DocumentEventData.pb(DocumentEventData.deserialize(await request.body()))
    except Exception as exc:
        raise ValidationError("Not a Firestore document event.") from exc
    document = event.value
    return document.name.rsplit("/", 1)[-1], {k: _value(v) for k, v in document.fields.items()}


def _value(value: Any) -> Any:
    kind = value.WhichOneof("value_type")
    match kind:
        case "null_value" | None:
            return None
        case "timestamp_value":
            return value.timestamp_value.ToDatetime(tzinfo=UTC).isoformat()
        case "map_value":
            return {k: _value(v) for k, v in value.map_value.fields.items()}
        case "array_value":
            return [_value(v) for v in value.array_value.values]
        case "geo_point_value":
            return {
                "latitude": value.geo_point_value.latitude,
                "longitude": value.geo_point_value.longitude,
            }
        case _:  # string, integer, double, boolean, bytes, reference
            return getattr(value, kind)
