"""The deployed service: every subdomain's router in one FastAPI app (ADR 0023).

`uvicorn apps.api:app` — in the container (Dockerfile) and locally (`make dev`).

This is the only file that knows every subdomain; nothing in kernel/ or src/ imports it.
Domains stay isolated in the code (import-linter), not in separate deployments.

Registering a subdomain: its router here, and its route in architecture/api-routes.json.
tests/test_domain_registry.py fails if the two disagree or a subdomain is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI

from kernel.app import make_app
from src.content.certifications.routes import router as content_certifications
from src.content.education.routes import router as content_education
from src.content.experience.routes import router as content_experience
from src.content.posts.routes import router as content_posts
from src.content.profile.routes import router as content_profile
from src.content.projects.routes import router as content_projects
from src.content.settings.routes import router as content_settings
from src.content.skills.routes import router as content_skills
from src.identity.admins.routes import router as identity_admins
from src.inbox.contact.routes import router as inbox_contact
from src.inbox.messages.routes import router as inbox_messages
from src.inbox.notifications.events import router as inbox_notifications_events
from src.media.library.routes import router as media_library
from src.media.processing.events import router as media_processing_events
from src.media.upload.routes import router as media_upload
from src.ops.audit.routes import router as ops_audit
from src.ops.backup.events import router as ops_backup_events
from src.ops.health.routes import router as ops_health

API_PREFIX = "/api/v1"

#: `<domain>/<subdomain>` → its public router, served at /api/v1/<domain>/<subdomain>.
ROUTES: dict[str, APIRouter] = {
    "content/profile": content_profile,
    "content/projects": content_projects,
    "content/skills": content_skills,
    "content/experience": content_experience,
    "content/education": content_education,
    "content/certifications": content_certifications,
    "content/posts": content_posts,
    "content/settings": content_settings,
    "identity/admins": identity_admins,
    "inbox/contact": inbox_contact,
    "inbox/messages": inbox_messages,
    "media/upload": media_upload,
    "media/library": media_library,
    "ops/health": ops_health,
    "ops/audit": ops_audit,
}

#: `<domain>/<subdomain>` → its events router, under /internal/<prefix> — called only by
#: Eventarc and Cloud Scheduler, with a signed token (kernel/events.py).
INTERNAL: dict[str, tuple[str, APIRouter]] = {
    "media/processing": ("/internal/events", media_processing_events),
    "inbox/notifications": ("/internal/events", inbox_notifications_events),
    "ops/backup": ("/internal/jobs", ops_backup_events),
}


def create_app() -> FastAPI:
    root = APIRouter()
    for route, router in ROUTES.items():
        root.include_router(router, prefix=f"{API_PREFIX}/{route}")
    for prefix, router in INTERNAL.values():
        root.include_router(router, prefix=prefix)
    return make_app(root, "api")


app = create_app()
