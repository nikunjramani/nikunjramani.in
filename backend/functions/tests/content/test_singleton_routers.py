"""profile and settings are singletons: GET/PUT/PATCH on `/`, no list, no id in the path,
one fixed document. Proven once here rather than trusting both call sites by eye."""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import patch

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from google.cloud.firestore_v1 import Client

from kernel.crud.repository import BaseRepository
from kernel.crud.service import CrudService
from kernel.http import make_app
from src.content.profile.repository import ProfileRepository
from src.content.profile.routes import get_profile_service
from src.content.profile.routes import router as profile_router
from src.content.profile.service import ProfileService
from src.content.settings.repository import SiteConfigRepository
from src.content.settings.routes import get_settings_service
from src.content.settings.routes import router as settings_router
from src.content.settings.service import SiteConfigService

ADMIN = {"uid": "admin-1", "email": "admin@example.com", "admin": True}

SINGLETON_DOMAINS = [
    pytest.param(
        profile_router,
        get_profile_service,
        ProfileService,
        ProfileRepository,
        {"name": "Nikunj Ramani", "headline": "Backend engineer", "visibility": "public"},
        id="profile",
    ),
    pytest.param(
        settings_router,
        get_settings_service,
        SiteConfigService,
        SiteConfigRepository,
        {"visibility": "public", "showBlog": False},
        id="settings",
    ),
]


@pytest.mark.parametrize(
    ("router", "get_service", "service_cls", "repo_cls", "payload"), SINGLETON_DOMAINS
)
def test_singleton_requires_admin(
    router: APIRouter,
    get_service: Callable[[], CrudService],  # type: ignore[type-arg]
    service_cls: type[CrudService],  # type: ignore[type-arg]
    repo_cls: type[BaseRepository],  # type: ignore[type-arg]
    payload: dict[str, object],
    db: Client,
    clean_collection: str,
) -> None:
    class ScratchRepo(repo_cls):  # type: ignore[misc, valid-type]
        collection = "_test_scratch"

    app = make_app(router, "test")
    app.dependency_overrides[get_service] = lambda: service_cls(ScratchRepo(db))
    client = TestClient(app)

    assert client.get("/").status_code == 401
    assert client.put("/", json=payload).status_code == 401


@pytest.mark.parametrize(
    ("router", "get_service", "service_cls", "repo_cls", "payload"), SINGLETON_DOMAINS
)
def test_singleton_create_read_patch(
    router: APIRouter,
    get_service: Callable[[], CrudService],  # type: ignore[type-arg]
    service_cls: type[CrudService],  # type: ignore[type-arg]
    repo_cls: type[BaseRepository],  # type: ignore[type-arg]
    payload: dict[str, object],
    db: Client,
    clean_collection: str,
) -> None:
    class ScratchRepo(repo_cls):  # type: ignore[misc, valid-type]
        collection = "_test_scratch"

    app = make_app(router, "test")
    app.dependency_overrides[get_service] = lambda: service_cls(ScratchRepo(db))
    client = TestClient(app)
    headers = {"Authorization": "Bearer x"}

    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        put = client.put("/", json=payload, headers=headers)
        assert put.status_code == 200
        assert put.json()["id"] == "main"

        got = client.get("/", headers=headers)
        assert got.status_code == 200
        assert got.json()["data"]["visibility"] == "public"

        patched = client.patch("/", json={"visibility": "draft"}, headers=headers)
        assert patched.status_code == 200
        assert patched.json()["data"]["visibility"] == "draft"


def test_singleton_get_before_any_write_is_404(db: Client, clean_collection: str) -> None:
    class ScratchRepo(ProfileRepository):
        collection = "_test_scratch"

    app = make_app(profile_router, "test")
    app.dependency_overrides[get_profile_service] = lambda: ProfileService(ScratchRepo(db))
    client = TestClient(app)

    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        assert client.get("/", headers={"Authorization": "Bearer x"}).status_code == 404


@pytest.mark.parametrize(
    ("router", "get_service", "service_cls", "repo_cls", "payload"), SINGLETON_DOMAINS
)
def test_singleton_public_read_needs_no_auth_and_hides_drafts(
    router: APIRouter,
    get_service: Callable[[], CrudService],  # type: ignore[type-arg]
    service_cls: type[CrudService],  # type: ignore[type-arg]
    repo_cls: type[BaseRepository],  # type: ignore[type-arg]
    payload: dict[str, object],
    db: Client,
    clean_collection: str,
) -> None:
    class ScratchRepo(repo_cls):  # type: ignore[misc, valid-type]
        collection = "_test_scratch"

    app = make_app(router, "test")
    app.dependency_overrides[get_service] = lambda: service_cls(ScratchRepo(db))
    client = TestClient(app)
    headers = {"Authorization": "Bearer x"}

    assert client.get("/public").status_code == 404  # nothing saved yet

    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        assert client.put("/", json=payload, headers=headers).status_code == 200
    public = client.get("/public")
    assert public.status_code == 200
    assert "audit" not in public.json()["data"]

    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        client.patch("/", json={"visibility": "draft"}, headers=headers)
    assert client.get("/public").status_code == 404
