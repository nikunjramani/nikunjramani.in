from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from kernel.security import AdminClaims
from src.identity.admins.repository import AuthUser
from src.identity.admins.schemas import AdminOut, GrantRequest
from src.identity.admins.service import AdminAccessService

router = APIRouter()


def get_admin_access_service() -> AdminAccessService:
    return AdminAccessService()


Service = Annotated[AdminAccessService, Depends(get_admin_access_service)]


def _out(user: AuthUser) -> AdminOut:
    return AdminOut(uid=user.uid, email=user.email, display_name=user.display_name)


@router.get("/", response_model=list[AdminOut], response_model_by_alias=True)
def list_admins(claims: AdminClaims, service: Service) -> list[AdminOut]:
    return [_out(u) for u in service.list_admins()]


@router.post("/", response_model=AdminOut, response_model_by_alias=True, status_code=201)
def grant_admin(payload: GrantRequest, claims: AdminClaims, service: Service) -> AdminOut:
    return _out(service.grant(payload.email, claims))


@router.delete("/{uid}", status_code=204)
def revoke_admin(uid: str, claims: AdminClaims, service: Service) -> Response:
    service.revoke(uid, claims)
    return Response(status_code=204)
