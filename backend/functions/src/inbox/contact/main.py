"""inbox/contact — entry point: deploys api_inbox_contact (public).

Abuse protection is Firebase App Check (ADR 0020), verified with the function's own identity —
no secret to bind."""

from kernel.http import make_function
from src.inbox.contact.routes import router

api_inbox_contact = make_function(router, name="api_inbox_contact")
