"""Wire shapes for ops/audit."""

from __future__ import annotations

from typing import Self

from kernel.records import Record
from shared.generated import AuditLog


class AuditLogOut(AuditLog):
    """An audit_log entry as the admin API returns it: its fields, flat, beside its id."""

    id: str

    @classmethod
    def of(cls, record: Record[AuditLog]) -> Self:
        return cls(id=record.id, **record.data.model_dump())
