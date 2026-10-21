---
paths:
  - "backend/**"
---

# Backend rules (one FastAPI service on Cloud Run)

Read `backend/README.md` before structural work; the `add-api-endpoint` skill has the
step-by-step. Decisions behind the code: `.docs/decisions/backend.md`. ADR 0017 (structure),
ADR 0023 (one service).

## Structure — enforced by import-linter and tests

- `src/<domain>/<subdomain>/` — one job, owns all its files: `routes.py` (HTTP only),
  `events.py` (only where an event or schedule starts the work — HTTP only too), `schemas.py`,
  `service.py` (rules, no HTTP), `repository.py` (the only Firestore SDK user;
  `inbox/contact/rate_limit.py`'s transaction is the one exception).
- Domains never import each other; subdomains never import siblings; **no `common/` folder**.
  The one exception is a **domain contract module** (ADR 0024): one file at a domain's root
  holding something its subdomains must agree on, and no logic. Today that's only
  `src/media/bucket.py` (the bucket's name and layout). Otherwise two subdomains needing the
  same convention each own their slice.
- `apps/api.py` assembles the service and is the only file that knows every subdomain;
  **nothing imports `apps/`**. `kernel/` is domain-free infrastructure only. `shared/generated`
  is generated models only.
- **No `__init__.py`** outside `shared/generated`. **Tests only in `backend/tests/`**,
  mirroring `apps/`, `src/` and `kernel/`.
- A content collection subclasses `kernel.crud` (`BaseRepository`, `CrudService`); copy
  `src/content/skills/`. Write the routes out; add only what's specific.

## A new subdomain needs two registrations

`tests/test_domain_registry.py` fails if either is missing:

1. its router in `apps/api.py` — `ROUTES` for `routes.py`, `INTERNAL` for `events.py`
2. its route in `architecture/api-routes.json` (the frontend's route names — run `make gen`)

…plus its folder in the import-linter contracts (`backend/pyproject.toml`), which the same test
checks. An `events.py` also needs its Eventarc trigger or Cloud Scheduler job in
`infra/terraform/modules/api`.

## Gotchas

- **`/internal/*` is on a public service.** Every events router carries
  `dependencies=[InternalCaller]` (`kernel/events.py`): a Google-signed token for one of
  `SERVICE_URL`'s audiences, from the runtime account. Never add an internal route without it.
- **Event handlers are idempotent.** Eventarc delivers at least once and retries any non-2xx:
  204 for "nothing to do", raise for "try again".
- **Never block the event loop.** CPU-bound or slow sync work in an `async def` route *or
  dependency* stalls every concurrent request (concurrency 80): a Firestore call, a token
  check, an App Check verify. Use a plain `def` (FastAPI runs it in the threadpool) or
  `run_in_threadpool`. `async def` is only for code that awaits or does nothing blocking.
- **Collection roots are `"/"` routes** but are reached without the slash through the Next.js
  rewrite. `kernel/app.py` serves both and never redirects — keep `redirect_slashes=False`.
- **Runtime config is `backend/deploy/<project>.yaml`**, secrets are `--set-secrets` in the
  Makefile's `deploy-api`; a new secret needs a Secret Manager version before the deploy.
- **Settings subclass `kernel.config.ServiceSettings`** and name their
  `required_in_production` fields; the class's getter goes in `SETTINGS` in `apps/api.py`, so a
  value missing in production fails the revision at startup. A new production setting goes in
  **both** deploy files in the same PR.
- **The service's shape (CPU, memory, concurrency, scaling) lives in the Makefile's
  `deploy-api`** — CI and break-glass both deploy through it. Don't add `gcloud run deploy`
  flags anywhere else.
- **Firestore `order_by(field)` silently drops documents missing that field**; composite queries
  need a composite index in the schema's `x-firestore.indexes`; `in` queries cap at 30 values.
- **Patch libraries where they're defined** in tests (`httpx.post`), not via another module's
  namespace — mypy `--strict` rejects non-re-exported attributes.
- **System Python may not be 3.13.** The Makefile asks `uv python find 3.13`.
- **This Windows box can't build blurhash-python** (it needs MSVC), so CI is the real test run.
  Everything else runs here: `uv sync --frozen --extra dev --no-install-package blurhash-python`,
  then pytest with a one-line `blurhash.py` stub (`def encode(*a, **k): return "LKO2"`) from the
  scratchpad on `PYTHONPATH`. Only `test_image.py`'s blurhash test fails against the stub; the
  emulator-backed tests skip.
- **Emulator-backed tests need no `gcloud` login** — `tests/conftest.py` gives the Admin SDK
  anonymous credentials; without the emulator running they skip.

## Every admin mutation

- takes `admin: Admin` in the route (`kernel.security`: verifies the token **and** the `admin`
  claim) and hands the service the `Actor` — services never see token claims,
- has its service build a `kernel.audit.AuditEntry` and pass it to the repository write, which
  commits change and entry in one batch (`CrudService` does it for you; `AuditWriter` only for a
  change outside Firestore),
- raises `kernel.errors` exceptions from services — never HTTP concepts. Every error reaches
  the client as `{"error": {code, message}}` (`kernel/app.py`); don't return `{"detail"}`.
