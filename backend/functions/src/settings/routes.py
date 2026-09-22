from fastapi import APIRouter

from shared.crud import make_crud_router
from shared.generated import SiteConfig
from src.settings.service import SiteConfigService

router = APIRouter()


def get_settings_service() -> SiteConfigService:
    return SiteConfigService()


router.include_router(
    make_crud_router(model=SiteConfig, get_service=get_settings_service, singleton_id="main")
)
