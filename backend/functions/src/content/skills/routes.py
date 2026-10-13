"""content/skills — admin HTTP routes for the `skills` collection.

HTTP only: authorise, delegate to the service, serialise. /reorder is declared before
/{doc_id} so it isn't captured as an id."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response

from kernel.security import AdminClaims
from shared.generated import Skill
from src.content.skills.schemas import ReorderIn, SkillOut
from src.content.skills.service import SkillService

router = APIRouter()


def get_skills_service() -> SkillService:
    return SkillService()


Service = Annotated[SkillService, Depends(get_skills_service)]


@router.get("/", response_model=list[SkillOut])
def list_skills(
    claims: AdminClaims,
    service: Service,
    visibility: Annotated[str | None, Query()] = None,
) -> list[SkillOut]:
    return [SkillOut.of(r) for r in service.list_records(visibility)]


@router.post("/", response_model=SkillOut, status_code=201)
def create_skills(payload: Skill, claims: AdminClaims, service: Service) -> SkillOut:
    return SkillOut.of(service.create(payload, claims, doc_id=None))


@router.post("/reorder", status_code=204)
def reorder_skills(body: ReorderIn, claims: AdminClaims, service: Service) -> Response:
    service.reorder(body.ids, claims)
    return Response(status_code=204)


@router.get("/{doc_id}", response_model=SkillOut)
def read_skills(doc_id: str, claims: AdminClaims, service: Service) -> SkillOut:
    return SkillOut.of(service.get(doc_id))


@router.patch("/{doc_id}", response_model=SkillOut)
def update_skills(
    doc_id: str, patch: dict[str, Any], claims: AdminClaims, service: Service
) -> SkillOut:
    """RFC 7386 merge patch: `null` removes a field."""
    return SkillOut.of(service.patch(doc_id, patch, claims))


@router.delete("/{doc_id}", status_code=204)
def delete_skills(doc_id: str, claims: AdminClaims, service: Service) -> Response:
    service.delete(doc_id, claims)
    return Response(status_code=204)
