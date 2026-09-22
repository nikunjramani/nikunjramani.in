"""System domain: liveness and other cross-cutting endpoints.

Deliberately the first domain built — it is the smallest thing that exercises the whole
adapter, so a mistake here is caught before it is copied thirteen times.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from shared.core.config import get_settings
from src.system.service import SystemService

router = APIRouter()


def get_system_service() -> SystemService:
    return SystemService()


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


@router.get("/resume")
def resume(service: Annotated[SystemService, Depends(get_system_service)]) -> RedirectResponse:
    url = service.get_resume_url()
    service.record_resume_download()
    return RedirectResponse(url, status_code=302)
