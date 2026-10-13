"""The `skills` collection."""

from kernel.crud.repository import BaseRepository
from shared.generated import Skill


class SkillRepository(BaseRepository[Skill]):
    collection = "skills"
    model = Skill
