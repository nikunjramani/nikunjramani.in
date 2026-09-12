"""POST /contact — the one public write endpoint that isn't behind admin auth.

The request model is deliberately narrower than the generated ContactMessage schema:
ip, userAgent, spamScore, read, replied, createdAt and expiresAt are all server-set, and
a client model that included them would let a POST body override its own audit trail.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.contact.service import ContactService

router = APIRouter()


class ContactRequest(BaseModel):
    # populate_by_name lets the field stay snake_case in Python while the wire format
    # (what the contact form actually POSTs) stays camelCase, matching the rest of the
    # frontend's JSON conventions.
    model_config = ConfigDict(populate_by_name=True)

    name: Annotated[str, Field(min_length=1, max_length=100)]
    email: EmailStr
    subject: Annotated[str, Field(max_length=200)] | None = None
    message: Annotated[str, Field(min_length=1, max_length=5000)]

    # Anti-abuse fields, not content. See src/contact/service.py for why failures here
    # are invisible to the response.
    honeypot: str = ""
    turnstile_token: Annotated[str, Field(alias="turnstileToken")] = ""


class ContactResponse(BaseModel):
    ok: bool = True
    message: str = "Thanks — I'll get back to you soon."


def get_contact_service() -> ContactService:
    return ContactService()


def _client_ip(request: Request) -> str:
    # Cloud Functions sit behind a load balancer; the real client address is the first
    # hop in X-Forwarded-For, not request.client.host (which would be the balancer).
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/contact", response_model=ContactResponse, status_code=202)
async def submit_contact(
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
        turnstile_token=payload.turnstile_token,
        ip=_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
    )
    return ContactResponse()
