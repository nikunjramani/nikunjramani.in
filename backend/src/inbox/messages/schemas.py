from kernel.crud.schemas import RecordOut
from shared.generated import ContactMessage


class MessageOut(RecordOut[ContactMessage]):
    """A contact_messages document as the admin API returns it."""
