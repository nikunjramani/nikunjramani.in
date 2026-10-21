"""content/experience — HTTP routes for the `experience` collection: admin
CRUD plus the public site's read.

HTTP only: authorise, delegate to the service, serialise. /public and /reorder are
declared before /{doc_id} so neither is captured as an id."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response

from kernel.security import AdminClaims
from shared.generated import Experience
from src.content.experience.schemas import ExperienceOut, ReorderIn
from src.content.experience.service import ExperienceService

router = APIRouter()


def get_experience_service() -> ExperienceService:
    return ExperienceService()


Service = Annotated[ExperienceService, Depends(get_experience_service)]


@router.get("/public", response_model=list[ExperienceOut], response_model_exclude_none=True)
def list_public_experience(service: Service) -> list[ExperienceOut]:
    """The public site's read — no auth: `public` documents only, in order (ADR 0022)."""
    return [ExperienceOut.of(r) for r in service.list_public()]


@router.get("/", response_model=list[ExperienceOut])
def list_experience(
    claims: AdminClaims,
    service: Service,
    visibility: Annotated[str | None, Query()] = None,
) -> list[ExperienceOut]:
    return [ExperienceOut.of(r) for r in service.list_records(visibility)]


@router.post("/", response_model=ExperienceOut, status_code=201)
def create_experience(payload: Experience, claims: AdminClaims, service: Service) -> ExperienceOut:
    return ExperienceOut.of(service.create(payload, claims, doc_id=None))


@router.post("/reorder", status_code=204)
def reorder_experience(body: ReorderIn, claims: AdminClaims, service: Service) -> Response:
    service.reorder(body.ids, claims)
    return Response(status_code=204)


@router.get("/{doc_id}", response_model=ExperienceOut)
def read_experience(doc_id: str, claims: AdminClaims, service: Service) -> ExperienceOut:
    return ExperienceOut.of(service.get(doc_id))


@router.patch("/{doc_id}", response_model=ExperienceOut)
def update_experience(
    doc_id: str, patch: dict[str, Any], claims: AdminClaims, service: Service
) -> ExperienceOut:
    """RFC 7386 merge patch: `null` removes a field."""
    return ExperienceOut.of(service.patch(doc_id, patch, claims))


@router.delete("/{doc_id}", status_code=204)
def delete_experience(doc_id: str, claims: AdminClaims, service: Service) -> Response:
    service.delete(doc_id, claims)
    return Response(status_code=204)
