---
paths:
  - "backend/**"
---

# Backend rules (Python Firebase Functions)

Read `backend/functions/README.md` before structural work; the `add-api-endpoint` skill has the
step-by-step. Decisions behind the code: `.docs/decisions/backend.md`. ADR 0017.

## Structure — enforced by import-linter and tests

- `src/<domain>/<subdomain>/` — one job, one deployed function `api_<domain>_<sub>`, owns all its
  files: `main.py` (the Firebase function), `routes.py` (HTTP only), `schemas.py`, `service.py`
  (rules, no HTTP), `repository.py` (the only Firestore SDK user; `inbox/contact/rate_limit.py`'s
  transaction is the one exception).
- Domains never import each other; subdomains never import siblings; **no `common/` folder**.
  Two subdomains needing the same convention each own their slice (`src/media/*/paths.py`).
- `kernel/` is domain-free infrastructure only. `shared/generated` is generated models only.
- **No `__init__.py`** outside `shared/generated`. **Tests only in `backend/functions/tests/`**,
  mirroring `src/` and `kernel/`.
- A content collection subclasses `kernel.crud` (`BaseRepository`, `CrudService`); copy
  `src/content/skills/`. Write the routes out; add only what's specific.

## A new subdomain needs four registrations

Missing any is **silent in production**; `tests/test_domain_registry.py` fails instead:

1. its domain's `FUNCTIONS` table (`src/<domain>/main.py`)
2. `architecture/api-routes.json` (generates the Next.js rewrites — run `make gen`)
3. the import-linter contracts in `backend/functions/pyproject.toml`
4. `http_functions` in `infra/terraform/modules/functions`

## Gotchas

- **Never construct `a2wsgi.ASGIMiddleware`** — its thread dies on fork and every request hangs.
  Use `kernel/wsgi_bridge.py`.
- **A `TestClient` pass doesn't prove the Firebase adapter works.** Changes to `kernel/http.py`,
  `kernel/wsgi_bridge.py` or `kernel/security.py` need a real request through the emulator
  (debug via `functions-framework`, not `firebase emulators:start --only functions`).
- **Secrets bound in a decorator need a Secret Manager version before deploy**, and aren't readable
  at import time. Only `on_contact_created` binds secrets.
- **Every function — HTTP, trigger, scheduled — must be in its domain's `FUNCTIONS` table**, or it
  never deploys. `tests/test_main_entrypoint.py` cross-checks.
- **Cold starts scale with imports.** Root `main.py` imports only `FUNCTION_TARGET`'s module; keep a
  subdomain's imports to what it uses. A `kernel/` or `shared/` change redeploys every function.
- **Firestore `order_by(field)` silently drops documents missing that field**; composite queries
  need a composite index in the schema's `x-firestore.indexes`; `in` queries cap at 30 values.
- **Patch libraries where they're defined** in tests (`httpx.post`), not via another module's
  namespace — mypy `--strict` rejects non-re-exported attributes.
- **System Python may not be 3.13.** The Makefile asks `uv python find 3.13`.
- **Firebase's CLI needs `requirements.txt` + a stdlib `venv/`**, separate from uv's `.venv/` —
  `make setup-backend` builds both.
- **This Windows box can't run the backend tests** (blurhash-python needs MSVC); CI runs them.
- **Emulator-backed tests need no `gcloud` login** — `tests/conftest.py` gives the Admin SDK
  anonymous credentials; without the emulator running they skip.

## Every admin mutation

- takes `claims: AdminClaims` (verifies the token **and** the `admin` claim),
- writes an `audit_log` entry through `kernel.audit.AuditWriter` (`CrudService` does it for you),
- raises `kernel.errors` exceptions from services — never HTTP concepts.
