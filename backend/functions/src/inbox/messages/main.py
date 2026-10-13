"""inbox/messages — entry point: deploys api_inbox_messages (admin)."""

from kernel.http import make_function
from src.inbox.messages.routes import router

api_inbox_messages = make_function(router, name="api_inbox_messages")
