from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from kernel.crud.schemas import RecordOut
from shared.generated import MediaAsset


class MediaAssetOut(RecordOut[MediaAsset]):
    """A media_assets document as the admin API returns it."""


class UpdateMetadataRequest(BaseModel):
    alt: Annotated[str, Field(min_length=1, max_length=200)]
    caption: Annotated[str, Field(max_length=300)] | None = None
