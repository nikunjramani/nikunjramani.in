from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class UploadRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content_type: Annotated[str, Field(alias="contentType")]
    size_bytes: Annotated[int, Field(alias="sizeBytes")]


class UploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    upload_url: Annotated[str, Field(alias="uploadUrl", serialization_alias="uploadUrl")]
    path: str
