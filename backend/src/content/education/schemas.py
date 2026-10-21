"""Wire shapes for content/education.

Requests are the Education model itself, validated by FastAPI against the generated
schema; responses carry the document id beside it."""

from kernel.crud.schemas import RecordOut, ReorderIn
from shared.generated import Education


class EducationOut(RecordOut[Education]):
    """A education document as the admin API returns it."""


__all__ = ["EducationOut", "ReorderIn"]
