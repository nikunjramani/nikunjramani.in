"""inbox/contact — entry point: deploys api_inbox_contact (public).

TURNSTILE_SECRET_KEY must have a Secret Manager version before deploy; without it in
production every submission is dropped (Turnstile fails closed)."""

from kernel.http import make_function
from src.inbox.contact.routes import router

api_inbox_contact = make_function(
    router, name="api_inbox_contact", secrets=["TURNSTILE_SECRET_KEY"]
)
