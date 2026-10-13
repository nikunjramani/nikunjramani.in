"""content/education — admin HTTP routes for the `education` collection.

HTTP only: authorise, delegate to the service, serialise. /reorder is declared before
/{doc_id} so it isn't captured as an id."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response

from kernel.security import AdminClaims
from shared.generated import Education
from src.content.education.schemas import EducationOut, ReorderIn
from src.content.education.service import EducationService

router = APIRouter()


def get_education_service() -> EducationService:
    return EducationService()


Service = Annotated[EducationService, Depends(get_education_service)]


@router.get("/", response_model=list[EducationOut])
def list_education(
    claims: AdminClaims,
    service: Service,
    visibility: Annotated[str | None, Query()] = None,
) -> list[EducationOut]:
    return [EducationOut.of(r) for r in service.list_records(visibility)]


@router.post("/", response_model=EducationOut, status_code=201)
def create_education(payload: Education, claims: AdminClaims, service: Service) -> EducationOut:
    return EducationOut.of(service.create(payload, claims, doc_id=None))


@router.post("/reorder", status_code=204)
def reorder_education(body: ReorderIn, claims: AdminClaims, service: Service) -> Response:
    service.reorder(body.ids, claims)
    return Response(status_code=204)


@router.get("/{doc_id}", response_model=EducationOut)
def read_education(doc_id: str, claims: AdminClaims, service: Service) -> EducationOut:
    return EducationOut.of(service.get(doc_id))


@router.patch("/{doc_id}", response_model=EducationOut)
def update_education(
    doc_id: str, patch: dict[str, Any], claims: AdminClaims, service: Service
) -> EducationOut:
    """RFC 7386 merge patch: `null` removes a field."""
    return EducationOut.of(service.patch(doc_id, patch, claims))


@router.delete("/{doc_id}", status_code=204)
def delete_education(doc_id: str, claims: AdminClaims, service: Service) -> Response:
    service.delete(doc_id, claims)
    return Response(status_code=204)
