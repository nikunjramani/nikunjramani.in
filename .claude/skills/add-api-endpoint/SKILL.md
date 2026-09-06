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

If the endpoint fits an existing domain, add it there. A **new** domain needs four extra steps —
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

**2 · Repository** — `backend/functions/repositories/`. Most collections just subclass:

```python
class ProjectRepository(BaseRepository[Project]):
    collection = "projects"
    model = Project
```

`BaseRepository` gives CRUD, pagination and ordering. Add a method only for a genuinely
collection-specific query.

**3 · Service** — `backend/functions/services/`. Business rules go here: slug uniqueness, publish
transitions, reorder transactions, cache busting. Raise domain exceptions from `core/errors.py`,
never HTTP ones.

**4 · Router** — `src/<domain>/routes.py`.

```python
@router.post("/projects", response_model=Project, status_code=201)
async def create_project(
    payload: ProjectCreate,
    _: None = Depends(require_admin),      # ← every admin route, no exceptions
    svc: ProjectService = Depends(get_project_service),
) -> Project:
    return await svc.create(payload)
```

- Every route under `admin/` needs `Depends(require_admin)` — signing in isn't enough, the
  `admin: true` claim is the gate
- Public routes that write need rate limiting: `Depends(rate_limit("3/hour"))`
- Declare `response_model` so the OpenAPI spec stays accurate

**5 · Audit** — every admin mutation writes `{ actor, action, collection, docId, before, after, at }`
to `audit_log`. Handle it in the service, not the router.

**6 · Cache** — a write that changes public content calls the Next.js revalidate endpoint, usually
via the `on_content_published` trigger. Without this, edits don't appear until ISR expires.

**7 · Tests** — required, all four:

- Unit test of the service with the repository mocked
- Integration test against the Firestore emulator
- Auth: no token → 401 · valid token without the claim → **403** · with the claim → 200
- Rate limit, if the route is public

## Triggers and scheduled jobs

Discrete functions, not FastAPI routes — `src/<domain>/triggers.py`, living with the domain they
belong to. `on_media_uploaded` goes in `src/media/`, not a global triggers directory.

Import heavy dependencies *inside* the handler; every top-level import runs on every cold start.

## Adding a new domain

Four steps, and forgetting any of them fails in a confusing way:

1. `mkdir src/<domain>/` with the shape above
2. Export the function:
   ```python
   # src/<domain>/__init__.py
   from shared.api import make_function
   from .routes import router

   api_<domain> = make_function(router, name="api_<domain>")
   ```
3. Import and re-export it in `backend/functions/main.py`
4. **Add the Firebase Hosting rewrite** — without it the function deploys fine and looks healthy,
   but the frontend gets a 404 that reads like a routing bug
   ```jsonc
   { "source": "/api/v1/<domain>/**", "function": "api_<domain>" }
   ```

Then add the domain to the Terraform `domains` map with its memory and `max_instances`.

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
