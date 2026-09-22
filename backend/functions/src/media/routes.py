"""Hand-written, not shared/crud.py's generic router: creation happens inside the
on_media_uploaded trigger, not a POST body — see src/media/service.py."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field

from shared.core.security import AdminClaims
from shared.generated import MediaAsset
from src.media.service import MediaService

router = APIRouter()


def get_media_service() -> MediaService:
    return MediaService()


class UploadRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content_type: Annotated[str, Field(alias="contentType")]
    size_bytes: Annotated[int, Field(alias="sizeBytes")]


class UploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    upload_url: Annotated[str, Field(alias="uploadUrl", serialization_alias="uploadUrl")]
    path: str


class RecordOut(BaseModel):
    id: str
    data: MediaAsset


@router.post("/upload-url", response_model=UploadResponse)
def request_upload_url(
    payload: UploadRequest,
    claims: AdminClaims,
    service: Annotated[MediaService, Depends(get_media_service)],
) -> UploadResponse:
    result = service.request_upload(
        content_type=payload.content_type, size_bytes=payload.size_bytes
    )
    return UploadResponse(upload_url=result["uploadUrl"], path=result["path"])


@router.get("/", response_model=list[RecordOut])
def list_media(
    claims: AdminClaims, service: Annotated[MediaService, Depends(get_media_service)]
) -> list[dict[str, object]]:
    return [{"id": r.id, "data": r.data} for r in service.list_all()]


@router.get("/{doc_id}", response_model=RecordOut)
def get_media(
    doc_id: str, claims: AdminClaims, service: Annotated[MediaService, Depends(get_media_service)]
) -> dict[str, object]:
    record = service.get(doc_id)
    return {"id": record.id, "data": record.data}


@router.delete("/{doc_id}", status_code=204)
def delete_media(
    doc_id: str, claims: AdminClaims, service: Annotated[MediaService, Depends(get_media_service)]
) -> Response:
    service.delete(doc_id)
    return Response(status_code=204)
