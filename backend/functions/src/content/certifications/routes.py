"""content/certifications — admin HTTP routes for the `certifications` collection.

HTTP only: authorise, delegate to the service, serialise. /reorder is declared before
/{doc_id} so it isn't captured as an id."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response

from kernel.security import AdminClaims
from shared.generated import Certification
from src.content.certifications.schemas import CertificationOut, ReorderIn
from src.content.certifications.service import CertificationService

router = APIRouter()


def get_certifications_service() -> CertificationService:
    return CertificationService()


Service = Annotated[CertificationService, Depends(get_certifications_service)]


@router.get("/", response_model=list[CertificationOut])
def list_certifications(
    claims: AdminClaims,
    service: Service,
    visibility: Annotated[str | None, Query()] = None,
) -> list[CertificationOut]:
    return [CertificationOut.of(r) for r in service.list_records(visibility)]


@router.post("/", response_model=CertificationOut, status_code=201)
def create_certifications(
    payload: Certification, claims: AdminClaims, service: Service
) -> CertificationOut:
    return CertificationOut.of(service.create(payload, claims, doc_id=None))


@router.post("/reorder", status_code=204)
def reorder_certifications(body: ReorderIn, claims: AdminClaims, service: Service) -> Response:
    service.reorder(body.ids, claims)
    return Response(status_code=204)


@router.get("/{doc_id}", response_model=CertificationOut)
def read_certifications(doc_id: str, claims: AdminClaims, service: Service) -> CertificationOut:
    return CertificationOut.of(service.get(doc_id))


@router.patch("/{doc_id}", response_model=CertificationOut)
def update_certifications(
    doc_id: str, patch: dict[str, Any], claims: AdminClaims, service: Service
) -> CertificationOut:
    """RFC 7386 merge patch: `null` removes a field."""
    return CertificationOut.of(service.patch(doc_id, patch, claims))


@router.delete("/{doc_id}", status_code=204)
def delete_certifications(doc_id: str, claims: AdminClaims, service: Service) -> Response:
    service.delete(doc_id, claims)
    return Response(status_code=204)
