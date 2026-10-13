"""inbox — entry point. Every Firebase function this domain deploys, mapped to the
subdomain `main` module that defines it. Nothing is imported here; see the root main.py."""

FUNCTIONS: dict[str, str] = {
    "api_inbox_contact": "src.inbox.contact.main",
    "api_inbox_messages": "src.inbox.messages.main",
    "on_contact_created": "src.inbox.notifications.main",
}
