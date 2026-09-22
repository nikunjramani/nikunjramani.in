from fastapi import APIRouter

from shared.crud import make_crud_router
from shared.generated import Profile
from src.profile.service import ProfileService

router = APIRouter()


def get_profile_service() -> ProfileService:
    return ProfileService()


router.include_router(
    make_crud_router(model=Profile, get_service=get_profile_service, singleton_id="main")
)
