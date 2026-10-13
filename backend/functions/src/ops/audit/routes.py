from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from kernel.security import AdminClaims
from src.ops.audit.service import AuditService

router = APIRouter()


def get_audit_service() -> AuditService:
    return AuditService()


@router.get("/")
def list_audit_log(
    claims: AdminClaims,
    service: Annotated[AuditService, Depends(get_audit_service)],
    collection: Annotated[str | None, Query()] = None,
    doc_id: Annotated[str | None, Query(alias="docId")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[dict[str, Any]]:
    return service.list_entries(collection=collection, doc_id=doc_id, limit=limit)
