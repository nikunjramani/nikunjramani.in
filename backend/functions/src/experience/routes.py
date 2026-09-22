from fastapi import APIRouter

from shared.crud import make_crud_router
from shared.generated import Experience
from src.experience.service import ExperienceService

router = APIRouter()


def get_experience_service() -> ExperienceService:
    return ExperienceService()


router.include_router(
    make_crud_router(model=Experience, get_service=get_experience_service, slugged=False)
)
