from fastapi import APIRouter

from shared.crud import make_crud_router
from shared.generated import Skill
from src.skills.service import SkillService

router = APIRouter()


def get_skills_service() -> SkillService:
    return SkillService()


router.include_router(make_crud_router(model=Skill, get_service=get_skills_service, slugged=False))
