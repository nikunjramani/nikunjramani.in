# Phase 3 · Backend

**~12 hours** · Status: ⬜ Not started

> **Goal:** A complete, tested Python API — every CRUD route the admin panel will need,
> the contact pipeline, and the background triggers — running on the emulator.

---

## Prerequisites

- [ ] [Phase 1](./phase-1-schemas.md) done — generated Pydantic models exist
- [ ] [03 · Security](../03-security.md) read
- [ ] Resend account + verified sending domain
- [ ] Cloudflare Turnstile site + secret keys

---

## Tasks

### 3.1 · Core

- [ ] `core/config.py` — `pydantic-settings`, env-driven, fails loudly on missing values
- [ ] `core/firebase.py` — Admin SDK init, emulator-aware
- [ ] `core/errors.py` — typed exceptions → consistent JSON error envelope
- [ ] `core/logging.py` — structured JSON logs for Cloud Logging
- [ ] `core/security.py` — verify ID token, assert `admin` claim
- [ ] `core/rate_limit.py` — Firestore-backed, per-IP and global

### 3.2 · Repository layer

- [ ] `BaseRepository[T]` — generic CRUD, pagination, ordering, soft delete
- [ ] One subclass per collection *(mostly a class name and a schema)*
- [ ] Firestore `Timestamp` ↔ ISO string conversion in exactly one place
- [ ] Transaction helper for reorder operations

> This layer is the only code allowed to import the Firestore SDK. That's what makes the services
> testable and what would make swapping the database a bounded task.

### 3.3 · Service layer

- [ ] `ProjectService` — slug uniqueness, publish transitions, reordering, cache busting
- [ ] `ContentService` — shared logic for the simpler collections
- [ ] `MediaService` — signed upload URLs, content-type allowlist, size caps
- [ ] `ContactService` — validation, Turnstile check, rate limit, spam scoring
- [ ] `EmailService` — Resend wrapper with a retry
- [ ] `AuditService` — before/after diff written to `audit_log`

### 3.4 · API

**Public**

- [ ] `GET /health`
- [ ] `POST /api/v1/contact`
- [ ] `GET /api/v1/resume` — 302 to a signed URL, counts downloads

**Admin** — every route requires the `admin` claim

- [ ] `projects` — list, get, create, update, delete, reorder, duplicate
- [ ] `skills` · `experience` · `education` · `certifications` · `posts` — full CRUD
- [ ] `PATCH profile`
- [ ] `POST media/upload-url` · `GET media` · `DELETE media/{id}`
- [ ] `GET messages` · `PATCH messages/{id}`
- [ ] `GET/PATCH settings`

**Wiring**

- [ ] `a2wsgi` wrapper exposing the FastAPI app as one `on_request` function
- [ ] CORS restricted to the real origins + localhost
- [ ] `/docs` reachable in dev, disabled in prod

### 3.5 · Triggers & scheduled jobs

- [ ] `on_contact_created` — spam score, then email via Resend
- [ ] `on_media_uploaded` — WebP conversion, thumbnails, blurhash, dimensions written back
- [ ] `on_content_published` — call the Next.js revalidate endpoint
- [ ] `nightly_backup` — export all collections to Storage as JSON

### 3.6 · Tests

- [ ] Unit tests for services, with repositories mocked
- [ ] Integration tests against the Firestore emulator
- [ ] Auth tests: no token → 401, valid token without claim → 403, with claim → 200
- [ ] Rate-limit tests
- [ ] Contact spam-path tests
- [ ] ≥ 80% coverage on services + repositories
- [ ] `mypy --strict` clean, `ruff` clean

---

## Definition of done

1. `/docs` shows the full API with accurate request/response models
2. Every admin route rejects a token without the `admin` claim
3. A contact submission on the emulator lands an email in your inbox
4. `make test` passes with ≥ 80% coverage
5. `mypy --strict` reports zero errors
6. Uploading an image produces WebP derivatives and a blurhash automatically

---

## Gotchas

**`a2wsgi` and the entrypoint.** Firebase's Python SDK expects a `flask.Request`-shaped handler.
Get one trivial route working through the emulator *before* building thirteen routers.

**Cold starts scale with imports.** Every top-level import runs on every cold start. Keep `main.py`
thin and import heavy things (image processing) inside the function that needs them.

**The emulator doesn't enforce production rules identically.** Test rules with the rules unit-testing
library too, not just by poking the emulator.

**Firestore `in` queries cap at 30 values** and composite queries need composite indexes. The index
file is generated from `x-firestore.indexes` — add the index when you add the query, not when prod
throws.

**Resend needs a verified domain** before it will send from `@nikunjramani.in`. Do the DNS records
early; verification isn't instant.

**Secrets aren't available at deploy time**, only at runtime. Reading a secret at import time fails
the deployment with an unhelpful error.

---

**Next:** [Phase 4 · Public Site](./phase-4-public-site.md)
