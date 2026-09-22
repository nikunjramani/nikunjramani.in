"""profile and settings are singletons: GET/PUT/PATCH on `/`, no list, no id in the path,
one fixed document. Proven once here rather than trusting both call sites by eye."""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import patch

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from google.cloud.firestore_v1 import Client

from shared.api import make_app
from shared.crud import ContentService
from shared.repositories.base import BaseRepository
from src.profile.repository import ProfileRepository
from src.profile.routes import get_profile_service
from src.profile.routes import router as profile_router
from src.settings.repository import SiteConfigRepository
from src.settings.routes import get_settings_service
from src.settings.routes import router as settings_router

ADMIN = {"uid": "admin-1", "email": "admin@example.com", "admin": True}

SINGLETON_DOMAINS = [
    pytest.param(
        profile_router,
        get_profile_service,
        ProfileRepository,
        {"name": "Nikunj Ramani", "headline": "Backend engineer", "visibility": "public"},
        id="profile",
    ),
    pytest.param(
        settings_router,
        get_settings_service,
        SiteConfigRepository,
        {"visibility": "public", "showBlog": False},
        id="settings",
    ),
]


@pytest.mark.parametrize(("router", "get_service", "repo_cls", "payload"), SINGLETON_DOMAINS)
def test_singleton_requires_admin(
    router: APIRouter,
    get_service: Callable[[], ContentService],  # type: ignore[type-arg]
    repo_cls: type[BaseRepository],  # type: ignore[type-arg]
    payload: dict[str, object],
    db: Client,
    clean_collection: str,
) -> None:
    class ScratchRepo(repo_cls):  # type: ignore[misc, valid-type]
        collection = "_test_scratch"

    app = make_app(router, "test")
    app.dependency_overrides[get_service] = lambda: ContentService(ScratchRepo(db))
    client = TestClient(app)

    assert client.get("/").status_code == 401
    assert client.put("/", json=payload).status_code == 401


@pytest.mark.parametrize(("router", "get_service", "repo_cls", "payload"), SINGLETON_DOMAINS)
def test_singleton_create_read_patch(
    router: APIRouter,
    get_service: Callable[[], ContentService],  # type: ignore[type-arg]
    repo_cls: type[BaseRepository],  # type: ignore[type-arg]
    payload: dict[str, object],
    db: Client,
    clean_collection: str,
) -> None:
    class ScratchRepo(repo_cls):  # type: ignore[misc, valid-type]
        collection = "_test_scratch"

    app = make_app(router, "test")
    app.dependency_overrides[get_service] = lambda: ContentService(ScratchRepo(db))
    client = TestClient(app)
    headers = {"Authorization": "Bearer x"}

    with patch("shared.core.security.auth.verify_id_token", return_value=ADMIN):
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
    app.dependency_overrides[get_profile_service] = lambda: ContentService(ScratchRepo(db))
    client = TestClient(app)

    with patch("shared.core.security.auth.verify_id_token", return_value=ADMIN):
        assert client.get("/", headers={"Authorization": "Bearer x"}).status_code == 404
