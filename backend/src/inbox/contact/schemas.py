"""The public contact form's wire shapes.

The request is deliberately narrower than the generated ContactMessage: ip, userAgent,
spamScore, read, replied, createdAt and expiresAt are server-set, and a client model that
included them would let a POST body forge its own metadata.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactRequest(BaseModel):
    # populate_by_name lets the field stay snake_case in Python while the wire format
    # (what the contact form actually POSTs) stays camelCase, matching the rest of the
    # frontend's JSON conventions.
    model_config = ConfigDict(populate_by_name=True)

    name: Annotated[str, Field(min_length=1, max_length=100)]
    email: EmailStr
    subject: Annotated[str, Field(max_length=200)] | None = None
    message: Annotated[str, Field(min_length=1, max_length=5000)]

    # Anti-abuse field, not content. See service.py for why a trip here is invisible to the
    # response. (The App Check token travels in the X-Firebase-AppCheck header, not the body.)
    honeypot: str = ""


class ContactResponse(BaseModel):
    ok: bool = True
    message: str = "Thanks — I'll get back to you soon."
