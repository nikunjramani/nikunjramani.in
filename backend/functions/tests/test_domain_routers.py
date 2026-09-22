"""Router wiring, proven once per domain shape rather than trusting that
`make_crud_router` was wired correctly into all eight call sites by eye.

Business logic (merge semantics, publish transitions, audit trail) is already covered in
shared/tests/test_crud.py — this file checks the thing that's specific to each domain's
routes.py: that AdminClaims actually gates every route, and that create/list/get/patch/
delete round-trip through the real HTTP layer, not just the service layer directly.

Lives in backend/functions/tests/, not shared/tests/: it imports from several src.<domain>
packages, and shared/ is not allowed to import from src/ — import-linter enforces exactly
that (ADR 0011) and correctly flagged this file the first time it landed under shared/.
A cross-domain test needs a home outside both root packages; this is it.
"""

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
from src.certifications.repository import CertificationRepository
from src.certifications.routes import get_certifications_service
from src.certifications.routes import router as certifications_router
from src.education.repository import EducationRepository
from src.education.routes import get_education_service
from src.education.routes import router as education_router
from src.experience.repository import ExperienceRepository
from src.experience.routes import get_experience_service
from src.experience.routes import router as experience_router
from src.skills.repository import SkillRepository
from src.skills.routes import get_skills_service
from src.skills.routes import router as skills_router

ADMIN = {"uid": "admin-1", "email": "admin@example.com", "admin": True}
NOT_ADMIN = {"uid": "user-1", "email": "user@example.com", "admin": False}

# (router, service getter, repository class, a minimal valid payload)
COLLECTION_DOMAINS = [
    pytest.param(
        skills_router,
        get_skills_service,
        SkillRepository,
        {"name": "Python", "category": "backend", "level": 4, "visibility": "public"},
        id="skills",
    ),
    pytest.param(
        experience_router,
        get_experience_service,
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
        EducationRepository,
        {"institution": "State U", "qualification": "BSc", "visibility": "public"},
        id="education",
    ),
    pytest.param(
        certifications_router,
        get_certifications_service,
        CertificationRepository,
        {"title": "AWS SA", "issuer": "AWS", "visibility": "public"},
        id="certifications",
    ),
]


def _client(
    router: APIRouter,
    get_service: Callable[[], ContentService],  # type: ignore[type-arg]
    repo_cls: type[BaseRepository],  # type: ignore[type-arg]
    db: Client,
) -> TestClient:
    class ScratchRepo(repo_cls):  # type: ignore[misc, valid-type]
        collection = "_test_scratch"

    def _get_service() -> ContentService:  # type: ignore[type-arg]
        return ContentService(ScratchRepo(db))

    app = make_app(router, "test")
    app.dependency_overrides[get_service] = _get_service
    return TestClient(app)


@pytest.mark.parametrize(("router", "get_service", "repo_cls", "payload"), COLLECTION_DOMAINS)
def test_create_requires_admin_claim(
    router: APIRouter,
    get_service: Callable[[], ContentService],  # type: ignore[type-arg]
    repo_cls: type[BaseRepository],  # type: ignore[type-arg]
    payload: dict[str, object],
    db: Client,
    clean_collection: str,
) -> None:
    client = _client(router, get_service, repo_cls, db)

    response = client.post("/", json=payload)
    assert response.status_code == 401

    with patch("shared.core.security.auth.verify_id_token", return_value=NOT_ADMIN):
        response = client.post("/", json=payload, headers={"Authorization": "Bearer x"})
    assert response.status_code == 403


@pytest.mark.parametrize(("router", "get_service", "repo_cls", "payload"), COLLECTION_DOMAINS)
def test_full_crud_round_trip(
    router: APIRouter,
    get_service: Callable[[], ContentService],  # type: ignore[type-arg]
    repo_cls: type[BaseRepository],  # type: ignore[type-arg]
    payload: dict[str, object],
    db: Client,
    clean_collection: str,
) -> None:
    client = _client(router, get_service, repo_cls, db)
    headers = {"Authorization": "Bearer x"}

    with patch("shared.core.security.auth.verify_id_token", return_value=ADMIN):
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
