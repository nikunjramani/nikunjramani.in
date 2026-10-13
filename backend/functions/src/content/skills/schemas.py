"""Wire shapes for content/skills.

Requests are the Skill model itself, validated by FastAPI against the generated
schema; responses carry the document id beside it."""

from kernel.crud.schemas import RecordOut, ReorderIn
from shared.generated import Skill


class SkillOut(RecordOut[Skill]):
    """A skills document as the admin API returns it."""


__all__ = ["ReorderIn", "SkillOut"]
