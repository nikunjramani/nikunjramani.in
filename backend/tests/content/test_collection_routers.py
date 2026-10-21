"""Router wiring for the collection subdomains, proven once per shape rather than trusting
eight hand-written routes.py files by eye.

The rules themselves (merge semantics, publish transitions, audit trail) are covered once in
tests/kernel/crud/test_service.py. This file checks what each subdomain's own routes.py
adds: that AdminClaims gates every route, and that create/list/get/patch/delete round-trip
through the real HTTP layer.
"""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import patch

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from google.cloud.firestore_v1 import Client

from kernel.app import make_app
from kernel.crud.repository import BaseRepository
from kernel.crud.service import CrudService
from src.content.certifications.repository import CertificationRepository
from src.content.certifications.routes import get_certifications_service
from src.content.certifications.routes import router as certifications_router
from src.content.certifications.service import CertificationService
from src.content.education.repository import EducationRepository
from src.content.education.routes import get_education_service
from src.content.education.routes import router as education_router
from src.content.education.service import EducationService
from src.content.experience.repository import ExperienceRepository
from src.content.experience.routes import get_experience_service
from src.content.experience.routes import router as experience_router
from src.content.experience.service import ExperienceService
from src.content.skills.repository import SkillRepository
from src.content.skills.routes import get_skills_service
from src.content.skills.routes import router as skills_router
from src.content.skills.service import SkillService

ADMIN = {"uid": "admin-1", "email": "admin@example.com", "admin": True}
NOT_ADMIN = {"uid": "user-1", "email": "user@example.com", "admin": False}

# (router, service getter, service class, repository class, a minimal valid payload)
COLLECTION_DOMAINS = [
    pytest.param(
        skills_router,
        get_skills_service,
        SkillService,
        SkillRepository,
        {"name": "Python", "category": "backend", "level": 4, "visibility": "public"},
        id="skills",
    ),
    pytest.param(
        experience_router,
        get_experience_service,
        ExperienceService,
        ExperienceRepository,
        {
            "company": "Acme",
            "role": "Engineer",
            "startDate": "2021-06",
            "current": True,
            "visibility": "public",
        },
        id="experience",
    ),
    pytest.param(
        education_router,
        get_education_service,
        EducationService,
        EducationRepository,
        {"institution": "State U", "qualification": "BSc", "visibility": "public"},
        id="education",
    ),
    pytest.param(
        certifications_router,
        get_certifications_service,
        CertificationService,
        CertificationRepository,
        {"title": "AWS SA", "issuer": "AWS", "visibility": "public"},
        id="certifications",
    ),
]


def _client(
    router: APIRouter,
    get_service: Callable[[], CrudService],  # type: ignore[type-arg]
    service_cls: type[CrudService],  # type: ignore[type-arg]
    repo_cls: type[BaseRepository],  # type: ignore[type-arg]
    db: Client,
) -> TestClient:
    class ScratchRepo(repo_cls):  # type: ignore[misc, valid-type]
        collection = "_test_scratch"

    def _get_service() -> CrudService:  # type: ignore[type-arg]
        return service_cls(ScratchRepo(db))

    app = make_app(router, "test")
    app.dependency_overrides[get_service] = _get_service
    return TestClient(app)


@pytest.mark.parametrize(
    ("router", "get_service", "service_cls", "repo_cls", "payload"), COLLECTION_DOMAINS
)
def test_create_requires_admin_claim(
    router: APIRouter,
    get_service: Callable[[], CrudService],  # type: ignore[type-arg]
    service_cls: type[CrudService],  # type: ignore[type-arg]
    repo_cls: type[BaseRepository],  # type: ignore[type-arg]
    payload: dict[str, object],
    db: Client,
    clean_collection: str,
) -> None:
    client = _client(router, get_service, service_cls, repo_cls, db)

    response = client.post("/", json=payload)
    assert response.status_code == 401

    with patch("kernel.security.auth.verify_id_token", return_value=NOT_ADMIN):
        response = client.post("/", json=payload, headers={"Authorization": "Bearer x"})
    assert response.status_code == 403


@pytest.mark.parametrize(
    ("router", "get_service", "service_cls", "repo_cls", "payload"), COLLECTION_DOMAINS
)
def test_full_crud_round_trip(
    router: APIRouter,
    get_service: Callable[[], CrudService],  # type: ignore[type-arg]
    service_cls: type[CrudService],  # type: ignore[type-arg]
    repo_cls: type[BaseRepository],  # type: ignore[type-arg]
    payload: dict[str, object],
    db: Client,
    clean_collection: str,
) -> None:
    client = _client(router, get_service, service_cls, repo_cls, db)
    headers = {"Authorization": "Bearer x"}

    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        created = client.post("/", json=payload, headers=headers)
        assert created.status_code == 201
        doc_id = created.json()["id"]

        listed = client.get("/", headers=headers)
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        fetched = client.get(f"/{doc_id}", headers=headers)
        assert fetched.status_code == 200

        patched = client.patch(f"/{doc_id}", json={"visibility": "draft"}, headers=headers)
        assert patched.status_code == 200
        assert patched.json()["data"]["visibility"] == "draft"

        deleted = client.delete(f"/{doc_id}", headers=headers)
        assert deleted.status_code == 204
        assert client.get(f"/{doc_id}", headers=headers).status_code == 404


@pytest.mark.parametrize(
    ("router", "get_service", "service_cls", "repo_cls", "payload"), COLLECTION_DOMAINS
)
def test_public_list_needs_no_auth_and_shows_only_public(
    router: APIRouter,
    get_service: Callable[[], CrudService],  # type: ignore[type-arg]
    service_cls: type[CrudService],  # type: ignore[type-arg]
    repo_cls: type[BaseRepository],  # type: ignore[type-arg]
    payload: dict[str, object],
    db: Client,
    clean_collection: str,
) -> None:
    client = _client(router, get_service, service_cls, repo_cls, db)
    headers = {"Authorization": "Bearer x"}

    with patch("kernel.security.auth.verify_id_token", return_value=ADMIN):
        client.post("/", json=payload, headers=headers)
        client.post("/", json={**payload, "visibility": "draft"}, headers=headers)

    listed = client.get("/public")
    assert listed.status_code == 200
    assert [r["data"]["visibility"] for r in listed.json()] == ["public"]
    assert "audit" not in listed.json()[0]["data"]
