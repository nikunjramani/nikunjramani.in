"""Wire shapes every admin CRUD route uses, whatever the model."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel

from kernel.records import Record


class RecordOut[T](BaseModel):
    """A document as the admin API returns it: the Firestore id beside the validated model."""

    id: str
    data: T

    @classmethod
    def of(cls, record: Record[T]) -> Self:
        return cls(id=record.id, data=record.data)


class ReorderIn(BaseModel):
    ids: list[str]
