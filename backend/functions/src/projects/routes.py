from typing import Annotated

from fastapi import APIRouter, Depends

from shared.core.security import AdminClaims
from shared.crud import RecordOut, make_crud_router
from shared.generated import Project
from src.projects.service import ProjectService

router = APIRouter()


def get_project_service() -> ProjectService:
    return ProjectService()


router.include_router(
    make_crud_router(model=Project, get_service=get_project_service, slugged=True)
)


@router.post("/{doc_id}/duplicate", response_model=RecordOut[Project], status_code=201)
def duplicate_project(
    doc_id: str,
    claims: AdminClaims,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> dict[str, object]:
    record = service.duplicate(doc_id, claims)
    return {"id": record.id, "data": record.data}
