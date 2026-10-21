from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from kernel.security import Admin
from src.media.upload.schemas import UploadRequest, UploadResponse
from src.media.upload.service import UploadService

router = APIRouter()


def get_upload_service() -> UploadService:
    return UploadService()


@router.post("/", response_model=UploadResponse)
def request_upload_url(
    payload: UploadRequest,
    admin: Admin,
    service: Annotated[UploadService, Depends(get_upload_service)],
) -> UploadResponse:
    result = service.request_upload(
        content_type=payload.content_type, size_bytes=payload.size_bytes
    )
    return UploadResponse(upload_url=result["uploadUrl"], path=result["path"])
