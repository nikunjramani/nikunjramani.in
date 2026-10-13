"""CrudService[T] — admin CRUD rules for any visibility/order collection.

Model-agnostic: the audit stamps, publish/unpublish transitions, RFC 7386 merge-patch and
reorder rules are identical for every such collection, so they live once here. A
subdomain's own service subclasses this and adds only what is specific to it
(ProjectService.duplicate). Routes stay in each subdomain (ADR 0017).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from kernel.audit import Action, AuditWriter
from kernel.crud.repository import BaseRepository
from kernel.errors import ConflictError, ValidationError
from kernel.records import Record
from kernel.security import actor_of
from kernel.timestamps import now_iso


def deep_merge(target: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """RFC 7386 JSON merge patch: objects merge recursively, `null` deletes a key, and
    anything else (including lists) replaces wholesale."""
    result = dict(target)
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class CrudService[T: BaseModel]:
    def __init__(
        self,
        repo: BaseRepository[T],
        *,
        audit: AuditWriter | None = None,
    ) -> None:
        self.repo = repo
        self._audit = audit if audit is not None else AuditWriter(repo.db)
        self._has_audit_field = "audit" in repo.model.model_fields

    # ── reads ────────────────────────────────────────────────────────

    def list_records(self, visibility: str | None = None) -> list[Record[T]]:
        return self.repo.list_all(visibility=visibility)

    def get(self, doc_id: str) -> Record[T]:
        return self.repo.require(doc_id)

    # ── writes ───────────────────────────────────────────────────────

    def create(
        self, payload: T, claims: dict[str, object], *, doc_id: str | None = None
    ) -> Record[T]:
        if doc_id is not None and self.repo.exists(doc_id):
            raise ConflictError(f"'{doc_id}' already exists.")
        uid, _ = actor_of(claims)
        data = payload.model_dump(mode="json", exclude_none=True)
        if self._has_audit_field:
            data["audit"] = self._stamp_new(data, uid)
        record = self.repo.create(self._validate(data), doc_id=doc_id)
        self._record("create", record.id, claims, before=None, after=self._dump(record))
        return record

    def upsert(self, doc_id: str, payload: T, claims: dict[str, object]) -> Record[T]:
        """Full replace at a known id — used by singletons (profile/main, site_config/main).

        createdAt/createdBy and the first publishedAt survive the replace; only a
        draft-to-public transition stamps a new publishedAt, exactly as patch() does.
        """
        uid, _ = actor_of(claims)
        existing = self.repo.get(doc_id)
        before = self._dump(existing) if existing else None
        data = payload.model_dump(mode="json", exclude_none=True)
        action: Action = "create"
        if before is not None:
            action = _transition(before.get("visibility"), data.get("visibility"))
        if self._has_audit_field:
            previous = dict(before.get("audit") or {}) if before else {}
            stamp = self._stamp_new(data, uid)
            audit = {**stamp, **{k: v for k, v in previous.items() if k != "updatedAt"}}
            audit["updatedAt"] = stamp["updatedAt"]
            if data.get("visibility") == "public" and not audit.get("publishedAt"):
                audit["publishedAt"] = stamp["updatedAt"]
            data["audit"] = audit
        record = self.repo.save(doc_id, self._validate(data))
        self._record(action, doc_id, claims, before=before, after=self._dump(record))
        return record

    def patch(self, doc_id: str, patch: dict[str, Any], claims: dict[str, object]) -> Record[T]:
        existing = self.repo.require(doc_id)
        before = self._dump(existing)

        patch = {k: v for k, v in patch.items() if k != "audit"}  # server-owned
        if "slug" in patch and patch["slug"] != before.get("slug"):
            raise ValidationError("slug is immutable: it is the document id and the public URL.")

        merged = deep_merge(before, patch)
        action = _transition(before.get("visibility"), merged.get("visibility"))
        if self._has_audit_field:
            audit = dict(merged.get("audit") or {})
            audit["updatedAt"] = now_iso()
            if action == "publish":
                audit["publishedAt"] = audit.get("publishedAt") or now_iso()
            merged["audit"] = audit

        record = self.repo.save(doc_id, self._validate(merged))
        self._record(action, doc_id, claims, before=before, after=self._dump(record))
        return record

    def delete(self, doc_id: str, claims: dict[str, object]) -> None:
        before = self._dump(self.repo.require(doc_id))
        self.repo.delete(doc_id)
        self._record("delete", doc_id, claims, before=before, after=None)

    def reorder(self, ids: list[str], claims: dict[str, object]) -> None:
        known = {r.id for r in self.repo.list_all()}
        unknown = [i for i in ids if i not in known]
        if unknown or len(set(ids)) != len(ids):
            raise ValidationError("Reorder needs each existing id exactly once.")
        self.repo.reorder(ids)
        self._record("reorder", None, claims, before=None, after={"ids": ids})

    # ── internal ─────────────────────────────────────────────────────

    def _validate(self, data: dict[str, Any]) -> T:
        try:
            return self.repo.model.model_validate(data)
        except PydanticValidationError as exc:
            first = exc.errors()[0]
            where = ".".join(str(p) for p in first["loc"]) or "body"
            raise ValidationError(f"{where}: {first['msg']}") from exc

    @staticmethod
    def _dump(record: Record[T] | None) -> dict[str, Any]:
        assert record is not None
        return record.data.model_dump(mode="json", exclude_none=True)

    @staticmethod
    def _stamp_new(data: dict[str, Any], uid: str) -> dict[str, Any]:
        now = now_iso()
        stamp: dict[str, Any] = {"createdAt": now, "updatedAt": now, "createdBy": uid}
        if data.get("visibility") == "public":
            stamp["publishedAt"] = now
        return stamp

    def _record(
        self,
        action: Action,
        doc_id: str | None,
        claims: dict[str, object],
        *,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
    ) -> None:
        self._audit.record(
            claims=claims,
            action=action,
            collection=self.repo.collection,
            doc_id=doc_id,
            before=before,
            after=after,
        )


def _transition(before_visibility: object, after_visibility: object) -> Action:
    if after_visibility == "public" and before_visibility != "public":
        return "publish"
    if before_visibility == "public" and after_visibility != "public":
        return "unpublish"
    return "update"
