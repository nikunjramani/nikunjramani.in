"""POST /api/v1/inbox/contact — the one public write endpoint without admin auth. Always
answers with the same success, whatever the anti-abuse checks decide (see service.py).

A plain `def`: App Check verification and the rate-limit transaction are blocking network
calls, so FastAPI runs the route in the threadpool rather than on the event loop."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from src.inbox.contact.app_check import HEADER as APP_CHECK_HEADER
from src.inbox.contact.schemas import ContactRequest, ContactResponse
from src.inbox.contact.service import ContactService

router = APIRouter()


def get_contact_service() -> ContactService:
    return ContactService()


def _client_ip(request: Request) -> str:
    # The first X-Forwarded-For hop is the visitor as seen through the Next.js rewrite and
    # Google's front end — but a client can send its own X-Forwarded-For, so this only
    # backs a best-effort per-IP limit. App Check, checked first, is the real gate.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/", response_model=ContactResponse, status_code=202)
def submit_contact(
    payload: ContactRequest,
    request: Request,
    service: Annotated[ContactService, Depends(get_contact_service)],
) -> ContactResponse:
    service.submit(
        name=payload.name,
        email=payload.email,
        subject=payload.subject,
        message=payload.message,
        honeypot=payload.honeypot,
        app_check_token=request.headers.get(APP_CHECK_HEADER, ""),
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
    )
    return ContactResponse()
