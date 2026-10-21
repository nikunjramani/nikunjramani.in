"""CrudService[T] — admin CRUD rules for any visibility/order collection.

Model-agnostic: the audit stamps, publish/unpublish transitions, RFC 7386 merge-patch and
reorder rules are identical for every such collection, so they live once here. A
subdomain's own service subclasses this and adds only what is specific to it
(ProjectService.duplicate). Routes stay in each subdomain (ADR 0017).

The public site reads through here too (ADR 0022): list_public/get_public apply the
visibility rule and drop the server-owned `audit` block before anything leaves the API.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from kernel.audit import Action, AuditEntry
from kernel.crud.repository import BaseRepository
from kernel.errors import ConflictError, NotFoundError, ValidationError
from kernel.records import Record
from kernel.security import Actor
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
    #: Visibility values get_public serves. A subclass widens it (projects add `unlisted`).
    reachable_by_url: frozenset[str] = frozenset({"public"})

    def __init__(self, repo: BaseRepository[T]) -> None:
        self.repo = repo
        self._has_audit_field = "audit" in repo.model.model_fields

    # ── reads ────────────────────────────────────────────────────────

    def list_records(self, visibility: str | None = None) -> list[Record[T]]:
        return self.repo.list_all(visibility=visibility)

    def get(self, doc_id: str) -> Record[T]:
        return self.repo.require(doc_id)

    # ── public reads (the site, no auth) ─────────────────────────────

    def list_public(self) -> list[Record[T]]:
        """Every `public` document in `order`. `unlisted` and `draft` are never listed."""
        return [self.to_public(r) for r in self.repo.list_all(visibility="public")]

    def get_public(self, doc_id: str) -> Record[T]:
        """One document, 404 unless its visibility is reachable by URL — a visitor guessing
        a draft's id gets the same answer as for an id that doesn't exist."""
        record = self.repo.get(doc_id)
        if record is None or _visibility(record) not in self.reachable_by_url:
            raise NotFoundError(f"{self.repo.model.__name__} '{doc_id}' not found.")
        return self.to_public(record)

    def to_public(self, record: Record[T]) -> Record[T]:
        """What a visitor may see of a record. Drops `audit` (it names the admin's uid);
        a subclass strips more (ProjectService: a confidential client's name and logo)."""
        if not self._has_audit_field:
            return record
        return Record(id=record.id, data=record.data.model_copy(update={"audit": None}))

    # ── writes ───────────────────────────────────────────────────────

    def create(self, payload: T, actor: Actor, *, doc_id: str | None = None) -> Record[T]:
        if doc_id is not None and self.repo.exists(doc_id):
            raise ConflictError(f"'{doc_id}' already exists.")
        doc_id = doc_id or self.repo.new_id()
        data = payload.model_dump(mode="json", exclude_none=True)
        if self._has_audit_field:
            data["audit"] = self._stamp_new(data, actor.uid)
        model = self._validate(data)
        entry = self._entry("create", doc_id, actor, before=None, after=model)
        return self.repo.create(model, doc_id=doc_id, audit=entry)

    def upsert(self, doc_id: str, payload: T, actor: Actor) -> Record[T]:
        """Full replace at a known id — used by singletons (profile/main, site_config/main).

        createdAt/createdBy and the first publishedAt survive the replace; only a
        draft-to-public transition stamps a new publishedAt, exactly as patch() does.
        """
        existing = self.repo.get(doc_id)
        before = self._dump(existing) if existing else None
        data = payload.model_dump(mode="json", exclude_none=True)
        action: Action = "create"
        if before is not None:
            action = _transition(before.get("visibility"), data.get("visibility"))
        if self._has_audit_field:
            previous = dict(before.get("audit") or {}) if before else {}
            stamp = self._stamp_new(data, actor.uid)
            audit = {**stamp, **{k: v for k, v in previous.items() if k != "updatedAt"}}
            audit["updatedAt"] = stamp["updatedAt"]
            if data.get("visibility") == "public" and not audit.get("publishedAt"):
                audit["publishedAt"] = stamp["updatedAt"]
            data["audit"] = audit
        model = self._validate(data)
        entry = self._entry(action, doc_id, actor, before=before, after=model)
        return self.repo.save(doc_id, model, audit=entry)

    def patch(self, doc_id: str, patch: dict[str, Any], actor: Actor) -> Record[T]:
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

        model = self._validate(merged)
        entry = self._entry(action, doc_id, actor, before=before, after=model)
        return self.repo.save(doc_id, model, audit=entry)

    def delete(self, doc_id: str, actor: Actor) -> None:
        before = self._dump(self.repo.require(doc_id))
        self.repo.delete(doc_id, audit=self._entry("delete", doc_id, actor, before=before))

    def reorder(self, ids: list[str], actor: Actor) -> None:
        known = {r.id for r in self.repo.list_all()}
        unknown = [i for i in ids if i not in known]
        if unknown or len(set(ids)) != len(ids):
            raise ValidationError("Reorder needs each existing id exactly once.")
        entry = AuditEntry(actor, "reorder", self.repo.collection, None, None, {"ids": ids})
        self.repo.reorder(ids, audit=entry)

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

    def _entry(
        self,
        action: Action,
        doc_id: str,
        actor: Actor,
        *,
        before: dict[str, Any] | None,
        after: T | None = None,
    ) -> AuditEntry:
        dumped = after.model_dump(mode="json", exclude_none=True) if after is not None else None
        return AuditEntry(actor, action, self.repo.collection, doc_id, before, dumped)


def _visibility(record: Record[Any]) -> object:
    return record.data.model_dump(mode="json").get("visibility")


def _transition(before_visibility: object, after_visibility: object) -> Action:
    if after_visibility == "public" and before_visibility != "public":
        return "publish"
    if before_visibility == "public" and after_visibility != "public":
        return "unpublish"
    return "update"
