---
name: add-api-endpoint
description: Add or modify an endpoint in the Python backend (one FastAPI service on Cloud Run). Use for any new API route, CRUD operation, event handler (Storage/Firestore via Eventarc), or scheduled job — this backend has strict domain/subdomain isolation and one-way layering that are easy to violate by accident.
---

# Adding a backend endpoint

Read [backend/README.md](../../../backend/README.md) first — it has the domain
map and the rules. → [ADR 0017](../../../.docs/adr/0017-bounded-context-domains.md) ·
[ADR 0023](../../../.docs/adr/0023-backend-as-one-cloud-run-service.md)

## First: which domain and subdomain?

```
src/<domain>/<subdomain>/      one job, served at /api/v1/<domain>/<subdomain>
├── routes.py       HTTP only: parse, authorise (AdminClaims), delegate, serialise
├── events.py       only if an event or schedule starts the work — HTTP only, InternalCaller
├── schemas.py      request / response models
├── service.py      the rules — no HTTP, raises kernel.errors
├── repository.py   its collection — the only Firestore SDK user
└── settings.py · storage.py · paths.py · …   anything else only this job needs
```

- A new route on an existing job → add it to that subdomain.
- A new job → a new subdomain. Don't stretch one subdomain over two jobs.
- **No `common/` folder, no sibling imports, no cross-domain imports.** If two subdomains need
  the same convention, each owns the slice it uses (see `src/media/*/paths.py` and
  `tests/media/test_layout.py`).
- **No `__init__.py`** — packages are implicit. **No tests under `src/`.**

## Is it a visibility/order content collection?

Copy `src/content/skills/`. Its `repository.py` subclasses `kernel.crud.repository.BaseRepository`,
its `service.py` subclasses `kernel.crud.service.CrudService` (audit stamps, publish/unpublish
transitions, RFC 7386 merge-patch, reorder, public reads), and its `routes.py` is written out in
full. A singleton (one fixed document) follows `src/content/profile/`. Add only what's specific
to the collection — `ProjectService.duplicate` is the example.

## Layering — one way only

`routes | events → schemas → service → repository → Firestore`, enforced by import-linter's
layers contract and `tests/test_import_rules.py`.

| Layer | Does | Must never |
|---|---|---|
| **routes** | Parse, `AdminClaims`, delegate, serialise | Contain rules or touch Firestore |
| **events** | `InternalCaller`, read the event (`kernel.events`), delegate | Contain rules or touch Firestore |
| **service** | Rules, orchestration | Know HTTP — no `Request`, no status codes |
| **repository** | Every Firestore SDK call for its collection | Contain rules |

The one exception: `src/inbox/contact/rate_limit.py`, whose check-and-increment is a single
transaction.

## Steps

**1 · Model** — generated from `architecture/schemas/` into `shared/generated`. Need a field?
Use the `add-schema-field` skill. Never hand-write a model.

**2 · Repository** — `repository.py`, only the operations this job needs on its collection.

**3 · Service** — `service.py`. Raise `kernel.errors` exceptions. Every admin mutation writes an
audit entry through `kernel.audit.AuditWriter` (`CrudService` already does).

**4 · Schemas + routes** — request/response models in `schemas.py` (wrap a record as
`RecordOut[Model]` from `kernel.crud.schemas`); routes in `routes.py`. Every admin route takes
`claims: AdminClaims` (`kernel.security`) — it verifies the token **and** the `admin` claim.
The one exception is a content subdomain's public read: `GET /public` (and `/public/{id}`), no
auth, returning `service.list_public()` / `get_public()` with `response_model_exclude_none=True`
— never a raw admin read (ADR 0022). Declare it before `/{doc_id}`.

**5 · Events and jobs** (only if the work starts from an event or a schedule) — `events.py`:

```python
router = APIRouter(dependencies=[InternalCaller])     # kernel.events — never omit it

@router.post("/<thing>-happened", status_code=204)
async def thing_happened(request: Request) -> Response:
    obj = await storage_object(request)               # or firestore_document(request)
    await run_in_threadpool(Service().handle, obj.name)  # off the event loop
    return Response(status_code=204)
```

Idempotent: Eventarc delivers at least once and retries any non-2xx. Then add the Eventarc
trigger or Cloud Scheduler job in `infra/terraform/modules/api` (the destination path is the
route; the identity is the runtime account; a scheduler's OIDC audience is the service URL).

**6 · Tests** — in `tests/<domain>/<sub>/`, mirroring the source:
- service unit tests with the repository faked (see `tests/inbox/contact/test_service.py`)
- route tests with the service overridden (see `tests/media/library/test_routes.py`)
- event tests posting a recorded payload (see `tests/media/processing/test_events.py`)
- repository/integration tests on the `db` fixture — they run against the Firestore emulator and
  skip without it (see `tests/content/projects/test_service.py`)

## Registering a new subdomain

`tests/test_domain_registry.py` fails `make test` until these are done:

1. **`backend/apps/api.py`** — import its router and add `"<domain>/<sub>": router` to `ROUTES`
   (an `events.py` router goes in `INTERNAL` with its `/internal/…` prefix). Not mounted → 404.
2. **`architecture/api-routes.json`** — add `"<sub>": "<domain>/<sub>"` under its domain, then
   `make gen` (the frontend's `API_ROUTES`).
3. **`backend/pyproject.toml`** — add the subdomain to its domain's independence contract and
   to the layers contract's `containers`.

A new **domain** also needs a place in the domain-independence contract.

## Secrets

Bound in the Makefile's `deploy-api` (`--set-secrets NAME=NAME:latest`), read through the
subdomain's `settings.py`. Terraform creates the container (`modules/secrets`); the owner adds
the value; a version must exist before the deploy.

## Verify

```bash
make lint          # ruff · mypy --strict · import-linter
make test          # emulator-backed tests skip unless the Firestore emulator is running
make dev-backend   # then check /docs shows the route with the right models
```

## Gotchas

- **Firestore `in` queries cap at 30 values.**
- **Composite queries need composite indexes** — add to `x-firestore.indexes` in the schema.
- **`/docs` is off in production** (`kernel/app.py`).
- **CPU-bound work in an `async def` blocks every concurrent request** — `run_in_threadpool` or
  a plain `def` route.
- **Collection roots are `"/"`** — reached as `/api/v1/<domain>/<sub>` through the rewrite;
  `kernel/app.py` handles the missing slash without redirecting.
