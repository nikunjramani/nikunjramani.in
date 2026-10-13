from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uid: str
    email: str | None
    display_name: Annotated[str | None, Field(serialization_alias="displayName")]


class GrantRequest(BaseModel):
    email: EmailStr
