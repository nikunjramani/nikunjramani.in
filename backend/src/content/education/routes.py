"""content/education — HTTP routes for the `education` collection: admin
CRUD plus the public site's read.

HTTP only: authorise, delegate to the service, serialise. /public and /reorder are
declared before /{doc_id} so neither is captured as an id."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response

from kernel.security import Admin
from shared.generated import Education
from src.content.education.schemas import EducationOut, ReorderIn
from src.content.education.service import EducationService

router = APIRouter()


def get_education_service() -> EducationService:
    return EducationService()


Service = Annotated[EducationService, Depends(get_education_service)]


@router.get("/public", response_model=list[EducationOut], response_model_exclude_none=True)
def list_public_education(service: Service) -> list[EducationOut]:
    """The public site's read — no auth: `public` documents only, in order (ADR 0022)."""
    return [EducationOut.of(r) for r in service.list_public()]


@router.get("/", response_model=list[EducationOut])
def list_education(
    admin: Admin,
    service: Service,
    visibility: Annotated[str | None, Query()] = None,
) -> list[EducationOut]:
    return [EducationOut.of(r) for r in service.list_records(visibility)]


@router.post("/", response_model=EducationOut, status_code=201)
def create_education(payload: Education, admin: Admin, service: Service) -> EducationOut:
    return EducationOut.of(service.create(payload, admin, doc_id=None))


@router.post("/reorder", status_code=204)
def reorder_education(body: ReorderIn, admin: Admin, service: Service) -> Response:
    service.reorder(body.ids, admin)
    return Response(status_code=204)


@router.get("/{doc_id}", response_model=EducationOut)
def read_education(doc_id: str, admin: Admin, service: Service) -> EducationOut:
    return EducationOut.of(service.get(doc_id))


@router.patch("/{doc_id}", response_model=EducationOut)
def update_education(
    doc_id: str, patch: dict[str, Any], admin: Admin, service: Service
) -> EducationOut:
    """RFC 7386 merge patch: `null` removes a field."""
    return EducationOut.of(service.patch(doc_id, patch, admin))


@router.delete("/{doc_id}", status_code=204)
def delete_education(doc_id: str, admin: Admin, service: Service) -> Response:
    service.delete(doc_id, admin)
    return Response(status_code=204)
