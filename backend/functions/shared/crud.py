"""Generic admin CRUD for content collections.

Eight domains (projects, skills, experience, education, certifications, posts, profile,
settings) are the same operation over a different model. The business rules — audit trail,
publish transitions, validation on merge — are identical, so they live here once.
`content_domain()` builds a whole standard domain (repository, service, router) from a
model; only a domain with genuinely specific logic (projects' duplicate) hand-writes its
own service. ADR 0011 splits domains for deploy isolation, ADR 0012/0016 share the rest.

Deliberately no `from __future__ import annotations` in this module: FastAPI resolves route
parameter annotations at import time, and the router factory below annotates parameters
with the runtime `model` variable.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from shared.core.errors import ConflictError, ValidationError
from shared.core.security import AdminClaims
from shared.core.timestamps import now_iso
from shared.repositories.base import BaseRepository, Record
from shared.services.audit import Action, AuditService


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
    ) -> None:
        self.repo = repo
        self._audit = audit if audit is not None else AuditService(repo.db)
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
        """Full replace at a known id — used by singletons (profile/main, site_config/main).

        createdAt/createdBy and the first publishedAt survive the replace; only a
        draft-to-public transition stamps a new publishedAt, exactly as patch() does.
        """
        uid, email = actor_of(claims)
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
        self._record(action, doc_id, uid, email, before=before, after=self._dump(record))
        return record

    def patch(self, doc_id: str, patch: dict[str, Any], claims: dict[str, object]) -> Record[T]:
        uid, email = actor_of(claims)
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


def _transition(before_visibility: object, after_visibility: object) -> Action:
    if after_visibility == "public" and before_visibility != "public":
        return "publish"
    if before_visibility == "public" and after_visibility != "public":
        return "unpublish"
    return "update"


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


@dataclass(frozen=True, slots=True)
class ContentDomain[T: BaseModel]:
    """Everything a standard content domain is: its repository class (tests subclass it to
    point at a scratch collection), the service factory routes depend on (tests override
    it), and the router `make_function` deploys."""

    repository: type[BaseRepository[T]]
    get_service: Callable[[], ContentService[T]]
    router: APIRouter


def content_domain[T: BaseModel](
    model: type[T],
    *,
    collection: str,
    slugged: bool = False,
    singleton_id: str | None = None,
) -> ContentDomain[T]:
    """Build a standard content domain from its model — see ADR 0016."""
    repository = cast(
        "type[BaseRepository[T]]",
        type(
            f"{model.__name__}Repository",
            (BaseRepository,),
            {"collection": collection, "model": model},
        ),
    )

    def get_service() -> ContentService[T]:
        return ContentService(repository())

    router = make_crud_router(
        model=model, get_service=get_service, slugged=slugged, singleton_id=singleton_id
    )
    return ContentDomain(repository=repository, get_service=get_service, router=router)


__all__ = [
    "ContentDomain",
    "ContentService",
    "RecordOut",
    "content_domain",
    "deep_merge",
    "make_crud_router",
]
