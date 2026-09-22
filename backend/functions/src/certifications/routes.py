from fastapi import APIRouter

from shared.crud import make_crud_router
from shared.generated import Certification
from src.certifications.service import CertificationService

router = APIRouter()


def get_certifications_service() -> CertificationService:
    return CertificationService()


router.include_router(
    make_crud_router(model=Certification, get_service=get_certifications_service, slugged=False)
)
