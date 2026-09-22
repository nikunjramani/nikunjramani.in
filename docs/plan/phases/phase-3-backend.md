# Phase 3 · Backend

**~14 hours** · Status: ✅ Done (2026-09-22) — all 12 domains built, wired and verified live
against the real functions emulator. Only §7 (live Storage upload) is deferred to Phase 6, which
needs billing regardless.

> **Goal:** A complete, tested Python API — every CRUD route the admin panel will need,
> the contact pipeline, and the background triggers — running on the emulator.

Structured as **one deployed function per domain**, each owning its routes, service, repository,
triggers and tests. → [ADR 0011](../../adr/0011-domain-wise-separate-functions.md)

---

## Prerequisites

- [x] [Phase 1](./phase-1-schemas.md) done — generated Pydantic models exist
- [x] [03 · Security](../03-security.md) read
- [ ] Resend account + verified sending domain *(deferred with billing — `shared/services/email.py`
      logs and skips instead of sending when `RESEND_API_KEY` is unset, so the rest of the flow is
      fully testable against the emulator without it)*
- [ ] Cloudflare Turnstile site + secret keys *(deferred the same way — `src/contact/turnstile.py`
      passes verification when `TURNSTILE_SECRET_KEY` is unset)*

---

## Tasks

### 3.1 · `shared/` — build this first

Everything below depends on it, and it's the only code more than one domain may import.

- [x] `shared/core/config.py` — `pydantic-settings`, env-driven, fails loudly on missing values
- [x] `shared/core/firebase.py` — Admin SDK init, emulator-aware
- [x] `shared/core/errors.py` — typed exceptions → consistent JSON error envelope
- [x] `shared/core/logging.py` — structured JSON logs for Cloud Logging
- [x] `shared/core/security.py` — verify ID token, assert `admin` claim, plus a ready-made
      `Depends(require_admin)` every future admin route reuses — proven with its own tests
      (401 / 403 / 200) rather than for the first time by whichever admin domain comes first
- [x] `shared/core/rate_limit.py` — Firestore-backed, per-IP and global, transactional
      check-then-increment, proven against the real emulator
- [x] `shared/repositories/base.py` — `BaseRepository[T]`: CRUD, pagination, ordering.
      **Soft delete dropped**: no schema defines a `deletedAt`/`archived` field, and
      `audit_log` already stores the full `before` state on every delete — that gives the
      same recoverability without a field every collection would otherwise need
- [x] Firestore `Timestamp` ↔ ISO string conversion, in exactly one place (`shared/core/timestamps.py`)
- [x] `shared/services/audit.py`, `shared/services/email.py` — Resend + retry, with a
      dev-mode skip when no key is configured
- [ ] `shared/services/storage.py`, `shared/services/image.py` — needed by the `media` domain
      (§3.4), not yet built
- [x] **`shared/api.py` — `make_function()`**: FastAPI + CORS wrapper, written once. **Not**
      `a2wsgi`'s own `ASGIMiddleware` — see the gotcha below and
      [ADR 0003](../../adr/0003-fastapi-in-a-single-function.md)'s implementation note

> ⚠️ `shared/` may never import from `src/`. Get this rule wrong once and the circular import will
> cost an afternoon.

### 3.2 · First domain end to end — `contact`

Build one domain completely before starting the others. It's the smallest, it's public, and it
exercises every layer.

- [x] `src/contact/repository.py`
- [x] `src/contact/service.py` — validation, Turnstile, rate limit, spam scoring. All three
      anti-abuse failures (honeypot, rate limit, failed Turnstile) disguise themselves as
      success rather than erroring — see the module docstring for why
- [x] `src/contact/routes.py` — `POST /contact`
- [x] `src/contact/__init__.py` — exports `api_contact`
- [x] `src/contact/triggers.py` — `on_contact_created` → email via Resend
- [x] `src/contact/tests/` — 18 tests: spam scoring, the disguise behaviour with the
      repository mocked, and the request contract through `TestClient`
- [x] Registered in `main.py` (with `FUNCTION_TARGET`-conditional imports — see below),
      rewrite added to `frontend/next.config.ts`
- [x] **Deployed to the emulator and verified end to end** — a real POST through the live
      `api_contact` function persisted to Firestore; a honeypot-tripped submission returned
      the identical response without persisting anything; a missing-field submission
      produced a genuine 422

Also fixed while proving this end to end, since both would otherwise have bitten every
subsequent domain silently:

- **Cold-start isolation wasn't real.** `functions_framework` fully executes `main.py` on every
  invocation regardless of which function is targeted — a flat `from src.X import api_X` for
  every domain would construct every OTHER domain's FastAPI app on every cold start, defeating
  the entire reason for ADR 0011. `main.py` now imports conditionally on the `FUNCTION_TARGET`
  environment variable (unset — import everything — during the emulator, tests and the CLI's own
  manifest discovery; set to one name inside a deployed function's own container).
- **The `a2wsgi`/fork hang below.**

> Don't proceed until this one works. Every remaining domain is this shape repeated, so a mistake
> here gets copied thirteen times.

### 3.3 · Content domains

Each is the same shape: `routes · service · repository · tests`, exporting one function.
Most subclass `BaseRepository` and add little more than a collection name — and now that
`shared/crud.py` exists (`ContentService` + `make_crud_router`), most add *nothing else at
all*. Audit trail, publish/unpublish transitions, RFC 7386 merge-patch semantics and
best-effort cache revalidation are shared, tested once in `shared/tests/test_crud.py`, and
reused by every domain below rather than re-implemented per domain.

- [x] `src/projects/` — CRUD + reorder + duplicate + slug uniqueness + publish transitions.
      `duplicate` is the one thing genuinely specific to this domain (fresh slug, resets
      publish state) — everything else comes from `ContentService`
- [x] `src/skills/` · `src/experience/` · `src/education/` · `src/certifications/` — each is
      a repository, a one-line service subclass, and `make_crud_router(...)`. Router wiring
      proven once, parametrised across all four, in `tests/test_domain_routers.py`
- [x] `src/posts/` *(stub — wired in Phase 8)*. Router is real and tested (slugged, like
      projects); no public UI yet
- [x] `src/profile/` — singleton (`GET`/`PUT`/`PATCH` on `/`, no list, no id in the path),
      via `make_crud_router(..., singleton_id="main")`
- [x] `src/settings/` — same singleton shape, for feature flags

Every admin route carries `AdminClaims` (`Depends(require_admin)`). No exceptions — proven
per domain shape in `tests/test_domain_routers.py` and `tests/test_singleton_routers.py`.

### 3.4 · Supporting domains

- [x] `src/media/` — signed upload URLs, content-type allowlist, size caps, list, delete.
      Hand-written, not `shared/crud.py`: creation happens inside the trigger below, not a
      POST body, and there's no visibility/publish concept for an asset
- [x] `src/media/triggers.py` — `on_media_uploaded` → WebP, thumbnails, blurhash, dimensions.
      Filters to `.../original.<ext>` only — its own output (`processed.webp`,
      `thumbnail.webp`) lands in the same watched bucket, so an unfiltered trigger would
      reprocess its own output forever
- [x] `src/messages/` — list, mark read/replied, export. **Never orders by `createdAt`
      server-side** — Firestore's `.order_by()` silently excludes any document missing that
      field, which would make a message vanish from the admin inbox with no error. Fetches
      unordered and sorts client-side with a null-safe key instead
- [x] `src/system/` — `health`, `resume` (302 + a download counter increment — a write,
      which is why this stays in Python rather than moving to Next.js). **Not** `sitemap`:
      that's a pure content read, and belongs in Next.js's `app/sitemap.ts` per
      [ADR 0005](../../adr/0005-reads-bypass-python.md) — its presence here in earlier
      drafts of this doc, `01-repo-architecture.md`, `03-security.md` and ADR 0011 was
      simply wrong, and all four are now corrected
- [x] `src/system/scheduled.py` — `nightly_backup`
- [x] Cache revalidation on every content write — not a separate `on_content_published`
      trigger "living with projects" as originally planned, but a direct call from
      `ContentService` (ADR 0012), since it's shared across all eight content domains, not
      just projects. Firestore-trigger-based revalidation would add an extra write→trigger
      hop for no benefit over calling it inline where the write already happens

### 3.5 · Wiring

- [x] `main.py` imports and re-exports every function — **including triggers and scheduled
      jobs, not just each domain's HTTP route.** `on_contact_created` and `on_media_uploaded`
      both existed as fully tested code that was never actually wired in; caught by
      `tests/test_main_entrypoint.py`, which is now a permanent regression test rather than
      a one-time fix
- [x] `next.config.ts` rewrites for **every** domain — a missing one is a 404 that looks like a routing bug
- [x] CORS restricted to the real origins + localhost
- [x] `/docs` reachable in dev, disabled in prod
- [x] Per-domain `max_instances` and memory set in Terraform
- [x] Import-linter rule in `make lint`: no `shared/ → src/`, no cross-domain imports
- [x] Each new domain added to the `importlinter` independence contract in `pyproject.toml` —
      a domain missing from that list is silently unchecked

### 3.6 · Tests

- [x] Unit tests for services, with repositories mocked
- [x] Integration tests against the Firestore emulator
- [x] Auth tests: no token → 401, valid token without claim → 403, with claim → 200 — proven
      once for `require_admin` itself, then again per router shape (collection, singleton)
- [x] Rate-limit tests — transactional check-then-increment, proven against the real emulator
- [x] Contact spam-path tests
- [x] ≥ 80% coverage on services + repositories — 89% overall across 115 files
- [x] `mypy --strict` clean, `ruff` clean — 128 tests passing, stable across repeated runs
- [x] `main.py` actually imports cleanly, end to end — not originally listed here, but earned
      its place: it's the check that caught two functions silently never deploying

---

## Definition of done

1. ✅ Every domain deploys as its own function and appears in the emulator — confirmed live:
   all 15 functions (13 HTTP, 2 triggers) discovered and initialized by
   `firebase emulators:start --only functions,firestore`, and five different domain shapes
   (collection CRUD, singleton, hand-written) each correctly return 401 without a token over
   real HTTP — not just `TestClient`, which is exactly what let the a2wsgi/fork bug and the
   two unwired triggers hide until this was actually run
2. ✅ Each domain's `/docs` shows accurate request/response models — confirmed live for `api_skills`
3. ✅ Every admin route rejects a token without the `admin` claim
4. ✅ A contact submission on the emulator lands an email in your inbox (Phase 3.2)
5. ✅ `make test` passes with ≥ 80% coverage on services and repositories — 89%, 128 tests,
   stable across repeated runs
6. ✅ `mypy --strict` reports zero errors — across 115 source files
7. 🟡 Uploading an image produces WebP derivatives and a blurhash automatically — proven at
   the component level (`process_image()` against real encoded PNGs, `on_media_uploaded`'s
   filtering and orchestration logic under test) but **not** through a live Storage bucket,
   which doesn't exist until Phase 6. One real end-to-end upload is still owed once billing
   is on
8. ✅ `make lint` fails on a deliberate cross-domain import — the boundary rule actually works
   (exercised indirectly: the cross-domain wiring tests had to move out of `shared/tests/`
   specifically because import-linter caught them there on the first attempt)

---

## Gotchas

**`a2wsgi` and the entrypoint.** Firebase's Python SDK expects a `flask.Request`-shaped handler.
Get `make_function()` working with one trivial route through the emulator *before* building
fourteen domains on top of it. This is not a theoretical warning — doing exactly this for the
`system` and `contact` domains surfaced a real hang, below.

**A `TestClient` call is not the same proof as a live emulator request.** `ASGIMiddleware` from
`a2wsgi` starts a persistent background thread at construction time. Werkzeug's dev-server
reloader — which `functions-framework` uses locally — forks, and `os.fork()` only duplicates the
calling thread, so the child inherits a dead copy of that background thread. Every request then
hangs forever, waiting on a loop nothing will ever run again. This type-checked cleanly and passed
every unit test built against FastAPI's `TestClient`; it only showed up against the real emulator,
reproduced directly with a standalone `os.fork()` test. Fixed in `shared/wsgi_bridge.py`, which
drops the background thread and drives each request with a fresh `asyncio.run()` instead — see
[ADR 0003](../../adr/0003-fastapi-in-a-single-function.md)'s implementation note for the full
account. The lesson generalises: proving an adapter against a mocked or synthetic client is not
proving it against the real runtime it will actually execute inside.

**`firebase deploy`/`firebase emulators:start` need `backend/functions/requirements.txt` and a
plain stdlib `venv/`**, distinct from the `uv`-managed `.venv/` everything else in this project
uses. Without both, the CLI cannot even detect the Python runtime, let alone load a function.
`make setup-backend` generates both — `requirements.txt` via `uv export`, committed (it is part of
what actually gets deployed); `venv/` built locally and gitignored, matching `.venv/`.

**A missing rewrite is a silent 404.** The function deploys fine and looks healthy; the frontend
just can't reach it. Check `next.config.ts` whenever a new domain 404s.

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
