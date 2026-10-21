# Backend — one FastAPI service, organised as domains and subdomains

The Python API behind nikunjramani.in: the only code that reads or writes Firestore — the
public site's reads (each content subdomain's `GET /public`), every admin read and write, plus
the background jobs ([ADR 0022](../.docs/adr/0022-backend-owns-all-data-access.md)). It runs as
**one Cloud Run service, `api`**, built from one image
([ADR 0023](../.docs/adr/0023-backend-as-one-cloud-run-service.md)).

The code is organised as **main domains**, each made of **subdomains**. A subdomain does one
job and owns every file for that job. Domains and subdomains never import each other — that
isolation lives in the code (import-linter), not in separate deployments.
→ [ADR 0017](../.docs/adr/0017-bounded-context-domains.md)

How a request moves through it: [CODE_FLOW §5–9](../.docs/CODE_FLOW.md#5--the-admin-edits-content).
Why each piece is written the way it is: [decisions/backend.md](../.docs/decisions/backend.md).

---

## Domain map

| Domain | Subdomain | Served at | Owns |
|---|---|---|---|
| **content** | `profile` | `/api/v1/content/profile` | `profile/main` |
| | `projects` | `/api/v1/content/projects` | `projects` (+ duplicate) |
| | `skills` | `/api/v1/content/skills` | `skills` |
| | `experience` | `/api/v1/content/experience` | `experience` |
| | `education` | `/api/v1/content/education` | `education` |
| | `certifications` | `/api/v1/content/certifications` | `certifications` |
| | `posts` | `/api/v1/content/posts` | `posts` |
| | `settings` | `/api/v1/content/settings` | `site_config/main` |
| **media** | `upload` | `/api/v1/media/upload` | signed upload URLs into `uploads/media/` |
| | `processing` | `/internal/events/media-uploaded` *(Eventarc: Storage)* | WebP + thumbnail + blurhash → new `media_assets` doc |
| | `library` | `/api/v1/media/library` | list, alt text, usage, delete for `media_assets` and its files |
| **inbox** | `contact` | `/api/v1/inbox/contact` (public) | App Check, honeypot, spam score, `_rate_limits` → new `contact_messages` doc |
| | `messages` | `/api/v1/inbox/messages` | read, mark, delete and CSV export of `contact_messages` |
| | `notifications` | `/internal/events/contact-created` *(Eventarc: Firestore)* | emails each new message to the owner (Resend) |
| **ops** | `health` | `/api/v1/ops/health` (public) | liveness |
| | `audit` | `/api/v1/ops/audit` | read-only view of `audit_log` |
| | `backup` | `/internal/jobs/backup` *(Cloud Scheduler, daily)* | JSON export of every collection |
| **identity** | `admins` | `/api/v1/identity/admins` | list, grant and revoke the `admin` custom claim |

`/api/v1/*` routes are admin-only unless marked *public*; content subdomains also serve an
unauthenticated `GET /public`. `/internal/*` accepts only Google-signed calls from the
service's own runtime account (`kernel/events.py`). Sign-in itself is Google in the browser; the
backend only verifies the resulting token and its `admin: true` claim.

---

## Layout

```
backend/
├── apps/
│   └── api.py                    the service: mounts every subdomain's router — the one file
│                                 that knows them all; nothing imports it
├── src/
│   └── <domain>/<subdomain>/     one job; owns all its files — no common/ folder anywhere
│       ├── routes.py             HTTP only: authorise, delegate, serialise
│       ├── events.py             (only where an event or job starts the work) HTTP only too
│       ├── schemas.py            request / response models
│       ├── service.py            the rules
│       ├── repository.py         its collection — the only Firestore SDK user
│       └── settings.py · storage.py · paths.py · …   whatever else this job alone needs
├── kernel/                       infrastructure every subdomain uses; knows no domain
│   ├── app.py                    make_app(): errors → JSON, CORS, /docs outside prod, no
│   │                             trailing-slash redirects
│   ├── events.py                 InternalCaller (who may call /internal/*), event readers
│   ├── security.py               verify_token(), AdminClaims, actor_of()
│   ├── audit.py                  AuditWriter — the audit_log entry every admin mutation writes
│   ├── crud/                     model-agnostic CRUD base: BaseRepository, CrudService
│   │                             (audit stamps, publish transitions, merge-patch, reorder,
│   │                             public reads), RecordOut / ReorderIn
│   └── config.py · errors.py · firebase.py · logging.py · records.py · timestamps.py
├── shared/generated/             Pydantic models generated from architecture/schemas
├── tests/                        every test, mirroring apps/, src/ and kernel/
├── deploy/                       <project>.yaml — the deployed service's non-secret config;
│                                 cleanup-policy.json — image retention in Artifact Registry
└── Dockerfile                    the image: uv-built venv + the code, uvicorn on $PORT
```

There are **no `__init__.py` files** (implicit namespace packages) except in
`shared/generated/`, where the generated one is the re-export behind
`from shared.generated import Project`. Tests are never mixed into `src/` or `kernel/`.

---

## The rules

Enforced, not recommended — `make lint` (import-linter) and `make test`
(`tests/test_import_rules.py`, `tests/test_domain_registry.py`):

1. **Main domains are independent.** `content`, `media`, `inbox`, `ops` and `identity` never
   import each other. They meet only through Firestore documents whose shape
   `architecture/schemas` fixes (`audit_log` is the main example).
2. **Subdomains are independent too — even within one domain.** No sibling imports and no
   `common/` folder. If two subdomains of a domain need the same thing, each owns the slice it
   uses. The media bucket layout is the example: `upload/paths.py`, `processing/paths.py` and
   `library/paths.py` each spell out their part, and `tests/media/test_layout.py` holds the
   three to one contract.
3. **Layers run one way inside a subdomain:** `routes | events → schemas → service →
   repository`. Routes and events never touch Firestore; services know nothing about HTTP and
   raise `kernel.errors`; only repositories import the Firestore SDK. One documented
   exception: `inbox/contact/rate_limit.py` keeps its check-and-increment in one transaction.
4. **`kernel/` imports no domain.** It holds only what is identical for every subdomain and
   carries no domain rule: the app builder, auth, event readers, the audit writer, the CRUD base.
5. **`shared/` is generated models only** and imports nothing of ours.
6. **Nothing imports `apps/`.** It assembles the service; it is never a dependency.

What looks like sharing but isn't:

- **Several domains writing `audit_log`.** They all call `kernel.audit.AuditWriter`; `ops/audit`
  reads. The schema is the contract.
- **Scanning another domain's collections by name.** The media library's "where is this image
  used?" check reads the content collections as opaque documents (`CONTENT_COLLECTIONS` in
  `src/media/library/repository.py`) and imports no content code.
- **`ops/backup` reading every collection.** Exporting is its whole job; it treats documents
  as opaque JSON and imports no other domain's code.

---

## Adding a subdomain

1. **Schema first**, if it stores something new: edit `architecture/schemas`, run `make gen`.
2. **Create `src/<domain>/<sub>/`** with `routes.py`, `schemas.py`, `service.py`,
   `repository.py`. For a visibility/order content collection, copy `src/content/skills/`:
   its repository and service subclass `kernel.crud`, and its routes are written out in full.
   Work started by an event or a schedule goes in `events.py`, with
   `APIRouter(dependencies=[InternalCaller])`.
3. **Tests** go in `tests/<domain>/<sub>/`.
4. **Register it** — `tests/test_domain_registry.py` fails until both are done:
   - `apps/api.py`: its router in `ROUTES` (or `INTERNAL` for `events.py`)
   - `architecture/api-routes.json`, then `make gen` (the frontend's route names)

   plus the domain's independence contract and the layers `containers` in `pyproject.toml`.
5. **An event or a schedule** also needs its Eventarc trigger or Cloud Scheduler job in
   `infra/terraform/modules/api`.
6. **A new secret** goes in `--set-secrets` in the Makefile's `deploy-api`, and must have a
   Secret Manager version before the deploy.
7. **Every admin mutation** writes an entry through `kernel.audit.AuditWriter`.

A new **domain** also needs an entry in the domain-independence contract.

---

## Running it

```bash
make setup-backend     # uv venv + uv sync
make dev               # emulators + the API on :8000 (reloading) + Next.js
make dev-backend       # just the API, against the emulators
make lint-backend      # ruff · mypy --strict · import-linter
make test-backend      # pytest; emulator-backed tests skip unless the emulator runs
```

`/docs` lists every route locally. Debug with VS Code's "Backend: debug the API". An event
handler is replayed by hand against the emulators — see
[RUNBOOK · replaying an event](../.docs/RUNBOOK.md#replaying-an-event-locally).

Deploys are CI's job (`.github/actions/cloud-run-deploy` → `make deploy-api`); see the
[RUNBOOK](../.docs/RUNBOOK.md#the-api-on-cloud-run).

---

## Gotchas

- **A subdomain not in `apps/api.py` is never served.** The registry test catches it.
- **Collection roots are declared at `/`** (`/api/v1/content/skills/`) but reached without the
  slash through the Next.js rewrite; `kernel/app.py` serves both and never redirects (a
  redirect would point at the Cloud Run host).
- **Event handlers must be idempotent.** Eventarc delivers at least once and retries any
  non-2xx; return 204 for "nothing to do", raise for "try again".
- **CPU-bound work in an `async def` route blocks every other request** — run it with
  `run_in_threadpool` (as `media/processing/events.py` does), or make the route a plain `def`.
- **Secrets aren't in `.env`.** Locally they're empty and the code skips what needs them
  (`send_email`); deployed, Cloud Run injects them from Secret Manager.
- **Composite queries need composite indexes**, declared in the schema's
  `x-firestore.indexes` (`"field:desc"`, `"tags:contains"`).
- **Running the emulator tests without a `gcloud` login works**: `tests/conftest.py` gives the
  Admin SDK anonymous credentials for the emulator.
- **This Windows box can't build blurhash-python** (no MSVC); CI runs the full suite.
