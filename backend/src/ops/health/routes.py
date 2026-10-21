from fastapi import APIRouter

from kernel.config import get_settings
from src.ops.health.schemas import Health

router = APIRouter()


@router.get("/", response_model=Health)
async def health() -> Health:
    settings = get_settings()
    return Health(
        status="ok", environment=settings.environment, project=settings.firebase_project_id
    )
