"""System domain: liveness and other cross-cutting endpoints.

Deliberately the first domain built — it is the smallest thing that exercises the whole
adapter, so a mistake here is caught before it is copied thirteen times.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from shared.core.config import get_settings

router = APIRouter()


class Health(BaseModel):
    status: str
    environment: str
    project: str


@router.get("/health", response_model=Health)
async def health() -> Health:
    settings = get_settings()
    return Health(
        status="ok",
        environment=settings.environment,
        project=settings.firebase_project_id,
    )
