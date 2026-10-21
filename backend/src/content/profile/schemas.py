"""Wire shapes for content/profile.

Requests are the Profile model itself, validated by FastAPI against the generated
schema; responses carry the document id beside it."""

from kernel.crud.schemas import RecordOut
from shared.generated import Profile


class ProfileOut(RecordOut[Profile]):
    """A profile document as the admin API returns it."""
