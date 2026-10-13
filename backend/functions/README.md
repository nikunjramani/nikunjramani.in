# Backend — domains, subdomains and the kernel

The Python API behind nikunjramani.in: every **write** the site makes, plus a few triggers
and jobs. Reads never come here; Next.js reads Firestore directly
([ADR 0005](../../docs/adr/0005-reads-bypass-python.md)).

The code is organised as **main domains**, each made of **subdomains**. A subdomain does one
job, owns every file for that job, and deploys as its own Cloud Function. Domains and
subdomains never import each other. → [ADR 0017](../../docs/adr/0017-bounded-context-domains.md)

---

## Domain map

| Domain | Subdomain | Deployed function | URL | Owns |
|---|---|---|---|---|
| **content** | `profile` | `api_content_profile` | `/api/v1/content/profile` | `profile/main` |
| | `projects` | `api_content_projects` | `/api/v1/content/projects` | `projects` (+ duplicate) |
| | `skills` | `api_content_skills` | `/api/v1/content/skills` | `skills` |
| | `experience` | `api_content_experience` | `/api/v1/content/experience` | `experience` |
| | `education` | `api_content_education` | `/api/v1/content/education` | `education` |
| | `certifications` | `api_content_certifications` | `/api/v1/content/certifications` | `certifications` |
| | `posts` | `api_content_posts` | `/api/v1/content/posts` | `posts` |
| | `settings` | `api_content_settings` | `/api/v1/content/settings` | `site_config/main` |
| **media** | `upload` | `api_media_upload` | `/api/v1/media/upload` | signed upload URLs into `uploads/media/` |
| | `processing` | `on_media_uploaded` | *Storage trigger* | WebP + thumbnail + blurhash → new `media_assets` doc |
| | `library` | `api_media_library` | `/api/v1/media/library` | list, alt text, delete for `media_assets` and its files |
| **inbox** | `contact` | `api_inbox_contact` | `/api/v1/inbox/contact` (public) | Turnstile, honeypot, spam score, `_rate_limits` → new `contact_messages` doc |
| | `messages` | `api_inbox_messages` | `/api/v1/inbox/messages` | read, mark, delete and CSV export of `contact_messages` |
| | `notifications` | `on_contact_created` | *Firestore trigger* | emails each new message to the owner (Resend) |
| **ops** | `health` | `api_ops_health` | `/api/v1/ops/health` (public) | liveness |
| | `audit` | `api_ops_audit` | `/api/v1/ops/audit` | read-only view of `audit_log` |
| | `backup` | `nightly_backup` | *scheduled, daily* | JSON export of every collection |
| **identity** | `admins` | `api_identity_admins` | `/api/v1/identity/admins` | list, grant and revoke the `admin` custom claim |

Every route is admin-only unless marked *public*. Sign-in itself is Google in the browser; the
backend only verifies the resulting token and its `admin: true` claim.

**Naming:** `src/<domain>/<sub>/` deploys as `api_<domain>_<sub>` and is served at
`/api/v1/<domain>/<sub>/…`. Next.js rewrites that path to the function
([`frontend/next.config.ts`](../../frontend/next.config.ts)).

---

## Layout

```
backend/functions/
├── main.py                       root entry point — merges every domain's FUNCTIONS table and
│                                 imports only the module FUNCTION_TARGET names
├── src/
│   └── <domain>/
│       ├── main.py               domain entry point: FUNCTIONS = {function name: subdomain module}
│       └── <subdomain>/          one job; owns all its files — no common/ folder anywhere
│           ├── main.py           subdomain entry point: defines its Firebase function(s)
│           ├── routes.py         HTTP only: authorise, delegate, serialise
│           ├── schemas.py        request / response models
│           ├── service.py        the rules
│           ├── repository.py     its collection — the only Firestore SDK user
│           └── settings.py · storage.py · paths.py · …   whatever else this job alone needs
├── kernel/                       infrastructure every subdomain uses; knows no domain
│   ├── http.py · wsgi_bridge.py  make_function(): FastAPI → Firebase HTTP function
│   ├── security.py               verify_token(), AdminClaims, actor_of()
│   ├── audit.py                  AuditWriter — the audit_log entry every admin mutation writes
│   ├── crud/                     model-agnostic CRUD base: BaseRepository, CrudService
│   │                             (audit stamps, publish transitions, merge-patch, reorder),
│   │                             RecordOut / ReorderIn
│   └── config.py · errors.py · firebase.py · logging.py · records.py · timestamps.py
├── shared/
│   └── generated/                Pydantic models generated from architecture/schemas
└── tests/                        every test, mirroring src/ and kernel/
    ├── content/projects/test_service.py · kernel/crud/test_service.py · …
    ├── conftest.py               Firestore-emulator fixtures
    └── test_main_entrypoint.py · test_domain_registry.py · test_import_rules.py
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
3. **Layers run one way inside a subdomain:** `main → routes → schemas → service → repository`.
   Routes never touch Firestore; services know nothing about HTTP and raise `kernel.errors`;
   only repositories import the Firestore SDK. One documented exception:
   `inbox/contact/rate_limit.py` keeps its check-and-increment in one transaction.
4. **`kernel/` imports no domain.** It holds only what is identical for every subdomain and
   carries no domain rule: the HTTP adapter, auth, the audit writer, the CRUD base classes.
5. **`shared/` is generated models only** and imports nothing of ours — ready to ship as its
   own package.

What looks like sharing but isn't:

- **Several domains writing `audit_log`.** They all call `kernel.audit.AuditWriter`; `ops/audit`
  reads. The schema is the contract.
- **Reading another domain's data** is a read, so it belongs in Next.js — e.g. the media
  library's "where is this image used?" check is
  `frontend/src/app/api/admin/media/[id]/usage/route.ts`.
- **`ops/backup` reading every collection.** Exporting is its whole job; it treats documents
  as opaque JSON and imports no other domain's code.

---

## Entry points

Three levels, so a cold start loads exactly one subdomain:

```python
# src/content/skills/main.py — the subdomain defines its function
api_content_skills = make_function(router, name="api_content_skills")

# src/content/main.py — the domain lists its functions, imports nothing
FUNCTIONS = {"api_content_skills": "src.content.skills.main", ...}

# main.py — merges every domain's table; imports only FUNCTION_TARGET's module
```

---

## Adding a subdomain

1. **Schema first**, if it stores something new: edit `architecture/schemas`, run `make gen`.
2. **Create `src/<domain>/<sub>/`** with `main.py`, `routes.py`, `schemas.py`, `service.py`,
   `repository.py`. For a visibility/order content collection, copy `src/content/skills/`:
   its repository and service subclass `kernel.crud`, and its routes are written out in full.
3. **Tests** go in `tests/<domain>/<sub>/`.
4. **Register it** — `tests/test_domain_registry.py` fails until all are done:
   - the domain's `src/<domain>/main.py` `FUNCTIONS` table
   - `pyproject.toml`: the domain's subdomain-independence contract and the layers `containers`
   - `frontend/next.config.ts`: `ROUTES`
   - `infra/terraform/modules/functions`: `http_functions`
5. **Secrets** are bound in code, `make_function(..., secrets=["NAME"])`, and must have a
   Secret Manager version before deploy.
6. **Every admin mutation** writes an entry through `kernel.audit.AuditWriter`.

A new **domain** also needs its own `src/<domain>/main.py`, a line in the root `main.py`, and
an entry in the domain-independence contract.

---

## Running it

```bash
make setup-backend     # uv venv + Firebase's own venv/ and requirements.txt
make lint-backend      # ruff · mypy --strict · import-linter
make test-backend      # pytest; emulator-backed tests skip unless the emulator runs
make dev               # emulators + Next.js
firebase deploy --only functions:api_content_projects    # one subdomain
```

Debug a subdomain directly with `functions-framework` (VS Code: "Backend: debug a subdomain",
e.g. `content_projects`), never through the Functions emulator — see
[docs/RUNBOOK.md](../../docs/RUNBOOK.md#debugging-vs-code).

---

## Gotchas

- **A function not in its domain's `FUNCTIONS` table never deploys.**
  `tests/test_main_entrypoint.py` imports `main.py` for real and checks every function,
  secret and instance limit.
- **Never construct `a2wsgi.ASGIMiddleware`.** Its background thread dies when the process
  forks and every request hangs. Use `kernel/wsgi_bridge.py`.
- **A change to `kernel/` or `shared/` redeploys every function.** Keep both small.
- **Secrets aren't available at import time,** only at request time.
- **Composite queries need composite indexes**, declared in the schema's
  `x-firestore.indexes` (`"field:desc"`, `"tags:contains"`).
- **Running the emulator tests without a `gcloud` login works**: `tests/conftest.py` gives the
  Admin SDK anonymous credentials for the emulator.
