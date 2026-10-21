from typing import Annotated

from fastapi import APIRouter, Depends, Query

from kernel.security import Admin
from src.ops.audit.schemas import AuditLogOut
from src.ops.audit.service import AuditService

router = APIRouter()


def get_audit_service() -> AuditService:
    return AuditService()


@router.get("/", response_model=list[AuditLogOut])
def list_audit_log(
    admin: Admin,
    service: Annotated[AuditService, Depends(get_audit_service)],
    collection: Annotated[str | None, Query()] = None,
    doc_id: Annotated[str | None, Query(alias="docId")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AuditLogOut]:
    entries = service.list_entries(collection=collection, doc_id=doc_id, limit=limit)
    return [AuditLogOut.of(e) for e in entries]
