"""Contact messages: write-only from the world, never client-readable. See ADR 0007."""

from __future__ import annotations

from shared.generated import ContactMessage
from shared.repositories.base import BaseRepository


class ContactRepository(BaseRepository[ContactMessage]):
    collection = "contact_messages"
    model = ContactMessage
