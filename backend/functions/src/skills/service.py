from google.cloud.firestore_v1 import Client

from shared.crud import ContentService
from shared.generated import Skill
from src.skills.repository import SkillRepository


class SkillService(ContentService[Skill]):
    def __init__(self, db: Client | None = None, *, repo: SkillRepository | None = None) -> None:
        super().__init__(repo if repo is not None else SkillRepository(db))
