from shared.generated import Skill
from shared.repositories.base import BaseRepository


class SkillRepository(BaseRepository[Skill]):
    collection = "skills"
    model = Skill
