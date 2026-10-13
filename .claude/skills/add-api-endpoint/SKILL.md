---
name: add-api-endpoint
description: Add or modify an endpoint in the Python Firebase Functions backend. Use for any new API route, CRUD operation, Firestore trigger, or scheduled job — this backend has strict domain/subdomain isolation and one-way layering that are easy to violate by accident.
---

# Adding a backend endpoint

Read [backend/functions/README.md](../../../backend/functions/README.md) first — it has the domain
map and the rules. → [ADR 0017](../../../docs/adr/0017-bounded-context-domains.md)

## First: which domain and subdomain?

```
src/<domain>/<subdomain>/      one job, one deployed function: api_<domain>_<subdomain>
├── main.py         the Firebase function(s) — make_function(router, ...) or a trigger
├── routes.py       HTTP only: parse, authorise (AdminClaims), delegate, serialise
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
transitions, RFC 7386 merge-patch, reorder), and its `routes.py` is written out in full. A
singleton (one fixed document) follows `src/content/profile/`. Add only what's specific to the
collection — `ProjectService.duplicate` is the example.

## Layering — one way only

`main → routes → schemas → service → repository → Firestore`, enforced by import-linter's
layers contract and `tests/test_import_rules.py`.

| Layer | Does | Must never |
|---|---|---|
| **routes** | Parse, `AdminClaims`, delegate, serialise | Contain rules or touch Firestore |
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

**5 · Entry point** — `main.py`:

```python
from kernel.http import make_function
from src.<domain>.<sub>.routes import router

api_<domain>_<sub> = make_function(router, name="api_<domain>_<sub>", secrets=["NAME"])
```

Bound secrets must have a Secret Manager version before deploy. Triggers and scheduled jobs are
defined in `main.py` too, with their logic in `service.py`.

**6 · Tests** — in `tests/<domain>/<sub>/`, mirroring the source:
- service unit tests with the repository faked (see `tests/inbox/contact/test_service.py`)
- route tests with the service overridden (see `tests/media/library/test_routes.py`)
- repository/integration tests on the `db` fixture — they run against the Firestore emulator and
  skip without it (see `tests/content/projects/test_service.py`)

## Registering a new subdomain

`tests/test_domain_registry.py` fails `make test` until all four are done — each one, missed,
fails silently in production:

1. **`src/<domain>/main.py`** — add `"api_<domain>_<sub>": "src.<domain>.<sub>.main"` to
   `FUNCTIONS` (triggers too, under their own names). Not listed → never deployed.
2. **`frontend/next.config.ts`** — add `"<domain>/<sub>"` to `ROUTES`. Missing → a 404 that reads
   like a routing bug.
3. **`backend/functions/pyproject.toml`** — add the subdomain to its domain's independence
   contract and to the layers contract's `containers`.
4. **`infra/terraform/modules/functions/main.tf`** — add `api_<domain>_<sub>` to
   `http_functions`. Missing → Cloud Run answers 403.

A new **domain** also needs `src/<domain>/main.py`, an import of its `FUNCTIONS` in the root
`main.py`, and a place in the domain-independence contract.

## Verify

```bash
make lint    # ruff · mypy --strict · import-linter
make test    # emulator-backed tests skip unless the Firestore emulator is running
make dev     # then check the subdomain's /docs shows the route with correct models
firebase deploy --only functions:api_<domain>_<sub>
```

## Gotchas

- **Secrets aren't available at import time**, only at request time.
- **Firestore `in` queries cap at 30 values.**
- **Composite queries need composite indexes** — add to `x-firestore.indexes` in the schema.
- **`/docs` must be disabled in production** (`kernel/http.py` does this).
- **A change under `kernel/` or `shared/` redeploys every function.**
- **Never construct `a2wsgi.ASGIMiddleware` directly** — use `kernel/wsgi_bridge.py`. Its thread
  dies when the dev server forks and every request hangs.
- **A `TestClient` pass does not prove the Firebase adapter works.** Changes to `kernel/http.py`
  or `kernel/wsgi_bridge.py` need a real request through the emulator.
