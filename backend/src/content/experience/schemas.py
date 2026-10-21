"""Wire shapes for content/experience.

Requests are the Experience model itself, validated by FastAPI against the generated
schema; responses carry the document id beside it."""

from kernel.crud.schemas import RecordOut, ReorderIn
from shared.generated import Experience


class ExperienceOut(RecordOut[Experience]):
    """A experience document as the admin API returns it."""


__all__ = ["ExperienceOut", "ReorderIn"]
