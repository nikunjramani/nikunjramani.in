from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from kernel.security import AdminClaims
from src.media.library.schemas import MediaAssetOut, UpdateMetadataRequest
from src.media.library.service import LibraryService

router = APIRouter()


def get_library_service() -> LibraryService:
    return LibraryService()


LibraryDep = Annotated[LibraryService, Depends(get_library_service)]


@router.get("/", response_model=list[MediaAssetOut])
def list_media(claims: AdminClaims, service: LibraryDep) -> list[MediaAssetOut]:
    return [MediaAssetOut.of(r) for r in service.list_all()]


@router.get("/{asset_id}", response_model=MediaAssetOut)
def get_media(asset_id: str, claims: AdminClaims, service: LibraryDep) -> MediaAssetOut:
    return MediaAssetOut.of(service.get(asset_id))


@router.patch("/{asset_id}", response_model=MediaAssetOut)
def update_media_metadata(
    asset_id: str, payload: UpdateMetadataRequest, claims: AdminClaims, service: LibraryDep
) -> MediaAssetOut:
    record = service.update_metadata(
        asset_id, alt=payload.alt, caption=payload.caption, claims=claims
    )
    return MediaAssetOut.of(record)


@router.delete("/{asset_id}", status_code=204)
def delete_media(asset_id: str, claims: AdminClaims, service: LibraryDep) -> Response:
    service.delete(asset_id, claims)
    return Response(status_code=204)
