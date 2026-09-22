"""Generic admin CRUD for content collections.

Eight domains (projects, skills, experience, education, certifications, posts, profile,
settings) are the same operation over a different model. The *business rules* — audit trail,
publish transitions, validation on merge, cache busting — are identical, so they live here
once. Each domain still owns its repository, its function, its tests and whatever is
genuinely specific to it (a project's slug uniqueness, say): ADR 0011 splits domains for
deploy isolation, not to forbid sharing infrastructure through shared/.

Deliberately no `from __future__ import annotations` in this module: FastAPI resolves route
parameter annotations at import time, and the router factory below annotates parameters
with the runtime `model` variable.
"""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from shared.core.errors import ConflictError, NotFoundError, ValidationError
from shared.core.security import AdminClaims
from shared.core.timestamps import now_iso
from shared.repositories.base import BaseRepository, Record
from shared.services.audit import Action, AuditService
from shared.services.revalidate import revalidate_tags


class RecordOut[T](BaseModel):
    """A document as the admin API returns it: the Firestore id beside the validated model."""

    id: str
    data: T


class ReorderIn(BaseModel):
    ids: list[str]


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


def actor_of(claims: dict[str, object]) -> tuple[str, str | None]:
    email = claims.get("email")
    return str(claims["uid"]), email if isinstance(email, str) else None


class ContentService[T: BaseModel]:
    def __init__(
        self,
        repo: BaseRepository[T],
        *,
        audit: AuditService | None = None,
        bust_cache: Callable[..., None] = revalidate_tags,
    ) -> None:
        self.repo = repo
        self._audit = audit if audit is not None else AuditService(repo.db)
        self._bust_cache = bust_cache
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
        uid, email = actor_of(claims)
        data = payload.model_dump(mode="json", exclude_none=True)
        if self._has_audit_field:
            data["audit"] = self._stamp_new(data, uid)
        record = self.repo.create(self._validate(data), doc_id=doc_id)
        self._record("create", record.id, uid, email, before=None, after=self._dump(record))
        return record

    def upsert(self, doc_id: str, payload: T, claims: dict[str, object]) -> Record[T]:
        """Full replace at a known id — used by singletons (profile/main, site_config/main)."""
        uid, email = actor_of(claims)
        before = self.repo.get(doc_id)
        data = payload.model_dump(mode="json", exclude_none=True)
        if self._has_audit_field:
            previous = self._dump(before).get("audit", {}) if before else {}
            data["audit"] = self._stamp_new(data, uid) | {
                k: v for k, v in previous.items() if k in ("createdAt", "createdBy")
            }
            data["audit"]["updatedAt"] = now_iso()
        record = self.repo.save(doc_id, self._validate(data))
        self._record(
            "update" if before else "create",
            doc_id,
            uid,
            email,
            before=self._dump(before) if before else None,
            after=self._dump(record),
        )
        return record

    def patch(self, doc_id: str, patch: dict[str, Any], claims: dict[str, object]) -> Record[T]:
        uid, email = actor_of(claims)
        existing = self.repo.require(doc_id)
        before = self._dump(existing)

        patch = {k: v for k, v in patch.items() if k != "audit"}  # server-owned
        if "slug" in patch and patch["slug"] != before.get("slug"):
            raise ValidationError("slug is immutable: it is the document id and the public URL.")

        merged = deep_merge(before, patch)
        action: Action = "update"
        if self._has_audit_field:
            audit = dict(merged.get("audit") or {})
            audit["updatedAt"] = now_iso()
            became_public = merged.get("visibility") == "public" != before.get("visibility")
            if became_public:
                audit["publishedAt"] = audit.get("publishedAt") or now_iso()
                action = "publish"
            elif before.get("visibility") == "public" and merged.get("visibility") != "public":
                action = "unpublish"
            merged["audit"] = audit

        record = self.repo.save(doc_id, self._validate(merged))
        self._record(action, doc_id, uid, email, before=before, after=self._dump(record))
        return record

    def delete(self, doc_id: str, claims: dict[str, object]) -> None:
        uid, email = actor_of(claims)
        before = self._dump(self.repo.require(doc_id))
        self.repo.delete(doc_id)
        self._record("delete", doc_id, uid, email, before=before, after=None)

    def reorder(self, ids: list[str], claims: dict[str, object]) -> None:
        uid, email = actor_of(claims)
        known = {r.id for r in self.repo.list_all()}
        unknown = [i for i in ids if i not in known]
        if unknown or len(set(ids)) != len(ids):
            raise ValidationError("Reorder needs each existing id exactly once.")
        self.repo.reorder(ids)
        self._record("reorder", None, uid, email, before=None, after={"ids": ids})

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
        uid: str,
        email: str | None,
        *,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
    ) -> None:
        self._audit.record(
            actor=uid,
            actor_email=email,
            action=action,
            collection=self.repo.collection,
            doc_id=doc_id,
            before=before,
            after=after,
        )
        self._bust_cache(self.repo.collection)


def _out(record: Record[Any]) -> dict[str, Any]:
    return {"id": record.id, "data": record.data}


def make_crud_router[T: BaseModel](
    *,
    model: type[T],
    get_service: Callable[[], ContentService[T]],
    slugged: bool = False,
    singleton_id: str | None = None,
) -> APIRouter:
    """Admin routes for one content collection.

    - collections: GET/POST `/`, GET/PATCH/DELETE `/{id}`, POST `/reorder`
    - `slugged=True`: the document id is the payload's slug (projects, posts)
    - `singleton_id="main"`: GET/PUT/PATCH `/` on one fixed document (profile, settings)

    Every route depends on AdminClaims. There is deliberately no way to build a public route
    with this factory: public reads bypass Python entirely (ADR 0005).
    """
    router = APIRouter()
    Service = Annotated[ContentService[Any], Depends(get_service)]  # noqa: N806
    Out = RecordOut[model]  # type: ignore[valid-type]  # noqa: N806

    if singleton_id is not None:
        sid = singleton_id

        @router.get("/", response_model=Out)
        def read_singleton(claims: AdminClaims, service: Service) -> dict[str, Any]:
            return _out(service.get(sid))

        @router.put("/", response_model=Out)
        def replace_singleton(
            payload: model,  # type: ignore[valid-type]
            claims: AdminClaims,
            service: Service,
        ) -> dict[str, Any]:
            return _out(service.upsert(sid, payload, claims))

        @router.patch("/", response_model=Out)
        def patch_singleton(
            patch: dict[str, Any], claims: AdminClaims, service: Service
        ) -> dict[str, Any]:
            return _out(service.patch(sid, patch, claims))

        return router

    @router.get("/", response_model=list[Out])
    def list_items(
        claims: AdminClaims,
        service: Service,
        visibility: Annotated[str | None, Query()] = None,
    ) -> list[dict[str, Any]]:
        return [_out(r) for r in service.list_records(visibility)]

    @router.post("/", response_model=Out, status_code=201)
    def create_item(
        payload: model,  # type: ignore[valid-type]
        claims: AdminClaims,
        service: Service,
    ) -> dict[str, Any]:
        doc_id = getattr(payload, "slug", None) if slugged else None
        return _out(service.create(payload, claims, doc_id=doc_id))

    @router.post("/reorder", status_code=204)
    def reorder_items(body: ReorderIn, claims: AdminClaims, service: Service) -> Response:
        service.reorder(body.ids, claims)
        return Response(status_code=204)

    @router.get("/{doc_id}", response_model=Out)
    def read_item(doc_id: str, claims: AdminClaims, service: Service) -> dict[str, Any]:
        return _out(service.get(doc_id))

    @router.patch("/{doc_id}", response_model=Out)
    def patch_item(
        doc_id: str, patch: dict[str, Any], claims: AdminClaims, service: Service
    ) -> dict[str, Any]:
        return _out(service.patch(doc_id, patch, claims))

    @router.delete("/{doc_id}", status_code=204)
    def delete_item(doc_id: str, claims: AdminClaims, service: Service) -> Response:
        service.delete(doc_id, claims)
        return Response(status_code=204)

    return router


__all__ = [
    "ContentService",
    "NotFoundError",
    "RecordOut",
    "deep_merge",
    "make_crud_router",
]
