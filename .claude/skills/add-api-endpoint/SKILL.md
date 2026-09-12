---
name: add-api-endpoint
description: Add or modify an endpoint in the Python Firebase Functions backend. Use for any new API route, CRUD operation, Firestore trigger, or scheduled job — this backend has strict one-way layering that is easy to violate by accident.
---

# Adding a backend endpoint

## First: which domain?

One deployed function per domain. Everything about a domain lives in
`backend/functions/src/<domain>/`. → [ADR 0011](../../../docs/adr/0011-domain-wise-separate-functions.md)

```
src/<domain>/
├── __init__.py     # exports api_<domain> via shared.api.make_function
├── routes.py       # FastAPI router
├── service.py      # business rules
├── repository.py   # Firestore access
├── triggers.py     # Firestore/Storage triggers for this domain
└── tests/
```

If the endpoint fits an existing domain, add it there. A **new** domain needs six extra steps —
see "Adding a new domain" below.

### Two import rules, both non-negotiable

- ❌ `shared/` importing from `src/` — circular dependency
- ❌ one domain importing another domain's `service` or `repository`

Cross-domain work goes through `shared/` or an event. `make lint` enforces both.

## Layering — one way only

```
router  →  service  →  repository  →  Firestore
   ↑          ↑            ↑
   └──── generated Pydantic models ────┘
```

| Layer | Does | Must never |
|---|---|---|
| **Router** | Parse, authorize, delegate, serialize | Contain business logic or touch Firestore |
| **Service** | Business rules, orchestration | Know what HTTP is — no `Request`, no status codes |
| **Repository** | Every Firestore SDK call | Contain business rules |

A router that imports the Firestore SDK is a bug. So is a service that raises `HTTPException`.

## Steps

**1 · Model** — already generated from `architecture/schemas/`. Need a new field? Use the
`add-schema-field` skill. Never hand-write a model.

**2 · Repository** — `src/<domain>/repository.py`. Most collections just subclass:

```python
class ProjectRepository(BaseRepository[Project]):
    collection = "projects"
    model = Project
```

`BaseRepository` gives CRUD, pagination and ordering. Add a method only for a genuinely
collection-specific query.

**3 · Service** — `src/<domain>/service.py`. Business rules go here: slug uniqueness, publish
transitions, reorder transactions, cache busting, rate limiting. Raise domain exceptions from
`shared/core/errors.py`, never HTTP ones. Rate limiting is a plain call inside the service, not a
router dependency — `RateLimiter(db).check(scope=..., identifier=..., limit=..., window_seconds=...)`
raises `RateLimitedError`, which the service either lets propagate (a real 429) or catches to
disguise as success (see `src/contact/service.py` for why the contact form does the latter).

**4 · Router** — `src/<domain>/routes.py`. Every admin route carries `AdminClaims`, which is
`Annotated[dict, Depends(require_admin)]` from `shared.core.security` — it verifies the bearer
token AND the `admin: true` claim, and hands back the decoded claims for the audit trail:

```python
from shared.core.security import AdminClaims

@router.post("/projects", response_model=Project, status_code=201)
async def create_project(
    payload: ProjectCreate,
    claims: AdminClaims,                                # ← every admin route, no exceptions
    svc: Annotated[ProjectService, Depends(get_project_service)],
) -> Project:
    return svc.create(payload, actor=claims["uid"])
```

Signing in isn't enough — the claim is the actual gate, and `require_admin` is already built and
tested (`shared/core/tests/test_security.py`), so a new domain does not re-prove it. Declare
`response_model` so the OpenAPI spec stays accurate.

**5 · Audit** — every admin mutation calls `AuditService(db).record(actor=..., action=...,
collection=..., doc_id=..., before=..., after=...)`. Handle it in the service, not the router.

**6 · Cache** — a write that changes public content calls the Next.js revalidate endpoint, usually
via the `on_content_published` trigger. Without this, edits don't appear until ISR expires.

**7 · Tests** — required, all four:

- Unit test of the service with the repository mocked (see `src/contact/tests/test_service.py`)
- Integration test against the Firestore emulator (see `shared/repositories/tests/`) — the `db`
  fixture from the root `conftest.py` skips automatically when the emulator isn't running, so
  `make test` still works offline
- Auth: no token → 401 · valid token without the claim → **403** · with the claim → 200 — already
  proven once for `require_admin` itself; a new admin domain doesn't need to re-derive this, just
  use `AdminClaims`
- Rate limit, if the route is public (see `shared/core/tests/test_rate_limit.py` for the pattern —
  a fresh scope per test avoids window collisions)

## Triggers and scheduled jobs

Discrete functions, not FastAPI routes — `src/<domain>/triggers.py`, living with the domain they
belong to. `on_media_uploaded` goes in `src/media/`, not a global triggers directory.

Import heavy dependencies *inside* the handler; every top-level import runs on every cold start.

## Adding a new domain

Six steps. Each of 3–5 fails silently rather than loudly — the domain works fine when invoked
directly (during local dev, tests, or manifest discovery), and only misbehaves in the one
situation those steps actually govern, which makes them easy to skip and forget.

1. `mkdir src/<domain>/` with the shape above
2. Export the function:
   ```python
   # src/<domain>/__init__.py
   from shared.api import make_function
   from .routes import router

   api_<domain> = make_function(router, name="api_<domain>")
   ```
3. **Add it to `main.py`'s `FUNCTION_TARGET`-conditional imports** — not a flat import. Without
   this, every domain's FastAPI app gets constructed on every OTHER domain's cold start, which
   defeats the entire reason for one-function-per-domain. See
   [ADR 0011](../../../docs/adr/0011-domain-wise-separate-functions.md)'s implementation note.
   ```python
   if _wanted("api_<domain>"):
       from src.<domain> import api_<domain>
   ```
4. **Add the rewrite** in `frontend/next.config.ts` — without it the function deploys fine and
   looks healthy, but the frontend gets a 404 that reads like a routing bug. Add the domain to the
   `DOMAINS` array:
   ```ts
   const DOMAINS = ["system", "contact", "<domain>"] as const;
   ```
   (Firebase Hosting rewrites don't apply — App Hosting is a different product and has none.)
5. **Add it to the import-linter contract** in `backend/functions/pyproject.toml`, or the domain's
   boundaries are silently unchecked.
6. Add the domain to the Terraform `domains` map with its memory and `max_instances`.

## Verify

```bash
make lint    # ruff + mypy --strict + import boundaries, all must be clean
make test    # ≥80% coverage on services and repositories
make dev     # then check the domain's /docs shows the route with correct models
```

Deploy just the domain you changed:

```bash
firebase deploy --only functions:api_<domain>
```

## Gotchas

- **Secrets aren't available at import time**, only at runtime. Reading one at module level fails
  the deploy with an unhelpful error.
- **Firestore `in` queries cap at 30 values.**
- **Composite queries need composite indexes** — add to `x-firestore.indexes` in the schema.
- **`/docs` must be disabled in production.**
- **A change under `shared/` redeploys every domain.** Worth knowing before refactoring it casually.
- **Never construct `a2wsgi.ASGIMiddleware` directly**, even to fix or extend `shared/api.py`. It
  starts a persistent background thread at construction time, which hangs every request forever
  once the process forks — which Werkzeug's dev-server reloader does locally. Reproduced directly
  with `os.fork()`. `shared/wsgi_bridge.py` is the fix; nothing should bypass it.
- **A `TestClient` pass does not prove the Firebase adapter works.** The bug above type-checked
  and passed every unit test — it only appeared against the real emulator. Any change to
  `shared/api.py` or `shared/wsgi_bridge.py` needs a real request through
  `firebase emulators:start --only functions,firestore`, not just `TestClient`.
