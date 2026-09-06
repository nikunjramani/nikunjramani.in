# Phase 3 · Backend

**~14 hours** · Status: ⬜ Not started

> **Goal:** A complete, tested Python API — every CRUD route the admin panel will need,
> the contact pipeline, and the background triggers — running on the emulator.

Structured as **one deployed function per domain**, each owning its routes, service, repository,
triggers and tests. → [ADR 0011](../../adr/0011-domain-wise-separate-functions.md)

---

## Prerequisites

- [ ] [Phase 1](./phase-1-schemas.md) done — generated Pydantic models exist
- [ ] [03 · Security](../03-security.md) read
- [ ] Resend account + verified sending domain
- [ ] Cloudflare Turnstile site + secret keys

---

## Tasks

### 3.1 · `shared/` — build this first

Everything below depends on it, and it's the only code more than one domain may import.

- [ ] `shared/core/config.py` — `pydantic-settings`, env-driven, fails loudly on missing values
- [ ] `shared/core/firebase.py` — Admin SDK init, emulator-aware
- [ ] `shared/core/errors.py` — typed exceptions → consistent JSON error envelope
- [ ] `shared/core/logging.py` — structured JSON logs for Cloud Logging
- [ ] `shared/core/security.py` — verify ID token, assert `admin` claim
- [ ] `shared/core/rate_limit.py` — Firestore-backed, per-IP and global
- [ ] `shared/repositories/base.py` — `BaseRepository[T]`: CRUD, pagination, ordering, soft delete
- [ ] Firestore `Timestamp` ↔ ISO string conversion, in exactly one place
- [ ] `shared/services/` — storage, email (Resend + retry), image, audit
- [ ] **`shared/api.py` — `make_function()`**: the FastAPI + `a2wsgi` + CORS wrapper, written once

> ⚠️ `shared/` may never import from `src/`. Get this rule wrong once and the circular import will
> cost an afternoon.

### 3.2 · First domain end to end — `contact`

Build one domain completely before starting the others. It's the smallest, it's public, and it
exercises every layer.

- [ ] `src/contact/repository.py`
- [ ] `src/contact/service.py` — validation, Turnstile, rate limit, spam scoring
- [ ] `src/contact/routes.py` — `POST /contact`
- [ ] `src/contact/__init__.py` — exports `api_contact`
- [ ] `src/contact/triggers.py` — `on_contact_created` → email via Resend
- [ ] `src/contact/tests/`
- [ ] Registered in `main.py`, Hosting rewrite added
- [ ] **Deployed to the emulator and verified end to end**

> Don't proceed until this one works. Every remaining domain is this shape repeated, so a mistake
> here gets copied thirteen times.

### 3.3 · Content domains

Each is the same shape: `routes · service · repository · tests`, exporting one function.
Most subclass `BaseRepository` and add little more than a collection name.

- [ ] `src/projects/` — CRUD + reorder + duplicate + slug uniqueness + publish transitions
- [ ] `src/skills/` · `src/experience/` · `src/education/` · `src/certifications/`
- [ ] `src/posts/` *(stub — wired in Phase 8)*
- [ ] `src/profile/` — single-document domain, `PATCH` only
- [ ] `src/settings/` — feature flags

Every admin route carries `Depends(require_admin)`. No exceptions.

### 3.4 · Supporting domains

- [ ] `src/media/` — signed upload URLs, content-type allowlist, size caps, list, delete
- [ ] `src/media/triggers.py` — `on_media_uploaded` → WebP, thumbnails, blurhash, dimensions
- [ ] `src/messages/` — list, mark read/replied, export
- [ ] `src/system/` — `health`, `resume` (302 to signed URL), `sitemap`
- [ ] `src/system/scheduled.py` — `nightly_backup`
- [ ] `on_content_published` trigger → Next.js revalidation *(lives with `projects`)*

### 3.5 · Wiring

- [ ] `main.py` imports and re-exports every function
- [ ] Hosting rewrites for **every** domain — a missing one is a 404 that looks like a routing bug
- [ ] CORS restricted to the real origins + localhost
- [ ] `/docs` reachable in dev, disabled in prod
- [ ] Per-domain `max_instances` and memory set in Terraform
- [ ] Import-linter rule in `make lint`: no `shared/ → src/`, no cross-domain imports

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

1. Every domain deploys as its own function and appears in the emulator
2. Each domain's `/docs` shows accurate request/response models
3. Every admin route rejects a token without the `admin` claim
4. A contact submission on the emulator lands an email in your inbox
5. `make test` passes with ≥ 80% coverage on services and repositories
6. `mypy --strict` reports zero errors
7. Uploading an image produces WebP derivatives and a blurhash automatically
8. `make lint` fails on a deliberate cross-domain import — the boundary rule actually works

---

## Gotchas

**`a2wsgi` and the entrypoint.** Firebase's Python SDK expects a `flask.Request`-shaped handler.
Get `make_function()` working with one trivial route through the emulator *before* building
fourteen domains on top of it.

**A missing Hosting rewrite is a silent 404.** The function deploys fine and looks healthy; the
frontend just can't reach it. Check the rewrite whenever a new domain 404s.

**Cross-domain imports are seductive.** `projects` will want something from `media`. Put it in
`shared/` or fire an event — the moment domains import each other, the boundary is gone and so is
the reason for splitting them.

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
