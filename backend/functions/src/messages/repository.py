from shared.generated import ContactMessage
from shared.repositories.base import BaseRepository


class MessageRepository(BaseRepository[ContactMessage]):
    collection = "contact_messages"
    model = ContactMessage
