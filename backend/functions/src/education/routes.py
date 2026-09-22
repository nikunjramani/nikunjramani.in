from fastapi import APIRouter

from shared.crud import make_crud_router
from shared.generated import Education
from src.education.service import EducationService

router = APIRouter()


def get_education_service() -> EducationService:
    return EducationService()


router.include_router(
    make_crud_router(model=Education, get_service=get_education_service, slugged=False)
)
