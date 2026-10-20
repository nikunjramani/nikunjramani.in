from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from kernel.security import AdminClaims
from src.media.library.schemas import MediaAssetOut, UpdateMetadataRequest, UsageOut
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


@router.get("/{asset_id}/usage", response_model=UsageOut)
def get_media_usage(asset_id: str, claims: AdminClaims, service: LibraryDep) -> UsageOut:
    return UsageOut(references=service.usage(asset_id))


@router.patch("/{asset_id}", response_model=MediaAssetOut)
def update_media_metadata(
    asset_id: str, payload: UpdateMetadataRequest, claims: AdminClaims, service: LibraryDep
) -> MediaAssetOut:
    record = service.update_metadata(
        asset_id, alt=payload.alt, caption=payload.caption, claims=claims
    )
    return MediaAssetOut.of(record)


@router.delete("/{asset_id}", status_code=204)
def delete_media(
    asset_id: str,
    claims: AdminClaims,
    service: LibraryDep,
    force: Annotated[bool, Query()] = False,
) -> Response:
    """409 while a content document still uses the asset, unless `force=true`."""
    service.delete(asset_id, claims, force=force)
    return Response(status_code=204)
