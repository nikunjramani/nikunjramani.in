"""Wire shapes for content/projects.

Requests are the Project model itself, validated by FastAPI against the generated
schema; responses carry the document id beside it."""

from kernel.crud.schemas import RecordOut, ReorderIn
from shared.generated import Project


class ProjectOut(RecordOut[Project]):
    """A projects document as the admin API returns it."""


__all__ = ["ProjectOut", "ReorderIn"]
