---
name: add-api-endpoint
description: Add or modify an endpoint in the Python Firebase Functions backend. Use for any new API route, CRUD operation, Firestore trigger, or scheduled job — this backend has strict one-way layering that is easy to violate by accident.
---

# Adding a backend endpoint

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

**4 · Router** — `backend/functions/api/routers/`. Public under `public/`, admin under `admin/`.

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

Separate discrete functions, not FastAPI routes — `backend/functions/triggers/` and `scheduled/`.
Import heavy dependencies *inside* the handler; every top-level import runs on every cold start.

## Verify

```bash
make lint    # ruff + mypy --strict, both must be clean
make test    # ≥80% coverage on services and repositories
make dev     # then check /docs shows the route with correct models
```

## Gotchas

- **Secrets aren't available at import time**, only at runtime. Reading one at module level fails
  the deploy with an unhelpful error.
- **Firestore `in` queries cap at 30 values.**
- **Composite queries need composite indexes** — add to `x-firestore.indexes` in the schema.
- **`/docs` must be disabled in production.**
