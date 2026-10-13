# CLAUDE.md

Context for working on this repository.

## What this is

The personal website at **nikunjramani.in** — portfolio, projects, writing. A server-rendered
Next.js site whose content lives in Firestore, edited through an admin panel on the site itself,
with a Python API owning every write.

**This repository is public.** Never commit secrets, credentials, personal contact details,
employer names, client names, or anything from a private engagement. Reach for a placeholder and
say so.

**Status:** Phases 0, 1, 3, 4 and 5 are implemented. Phase 6 is deployed —
`https://nikunjramani.in` is live over HTTPS, with a few launch checks still open
(see [Phase 6](./docs/plan/phases/phase-6-deploy.md)). Production admin claim and
signed uploads are verified. Backend: 172 tests (61 need the Firestore emulator). Billing is enabled. Local
development still uses emulators. Phase 2 needs the owner's content.
Full plan: [`docs/plan/`](./docs/plan/README.md) · ADRs: [`docs/adr/`](./docs/adr/README.md)

## Stack

| | |
|---|---|
| Frontend | Next.js 16 App Router · TypeScript strict · Tailwind v4 · shadcn/ui |
| Backend | Python 3.13 · FastAPI on Cloud Functions for Firebase (2nd gen) |
| Data | Cloud Firestore · Firebase Storage · Firebase Auth |
| Hosting | Firebase App Hosting |
| Infra | Terraform (`google` + `google-beta`) |

## Layout

```
architecture/   JSON Schemas — the single source of truth for every model
frontend/       Next.js app: (site) public + (admin) private
backend/        Python Firebase Functions — src/<domain>/<subdomain>, kernel/, shared/ (models)
infra/          Terraform modules + Firestore/Storage rules
docs/plan/      The build plan, per phase
docs/adr/       Architecture decision records
```

## Commands

```bash
make setup   # install both sides
make dev     # Next.js dev server + Firebase emulators
make gen     # regenerate models from architecture/schemas  ← after ANY schema edit
make validate # validate schemas + example fixtures
make lint    # eslint + ruff + mypy --strict + import-linter + terraform fmt
make test    # vitest + pytest
make deploy  # terraform apply + firebase deploy
```

CI today is only `.github/workflows/schemas.yml` (validate + codegen drift). Lint and test
workflows are Phase 7 — until then, run `make lint` and `make test` yourself before pushing.

---

## The seven rules

These are load-bearing. Each has an ADR behind it — read it before proposing a change.

**1 · Never hand-edit generated code.**
`frontend/src/generated/` and `backend/functions/shared/generated/` come from `architecture/schemas/`.
Edit the schema, run `make gen`. CI fails on drift. → [ADR 0006](./docs/adr/0006-json-schema-source-of-truth.md)

**2 · Reads never touch Python.**
Next.js Server Components read Firestore directly via the Admin SDK. Python handles writes only.
Never propose routing page data through the API — cold starts would sit on the read path.
→ [ADR 0005](./docs/adr/0005-reads-bypass-python.md)

**3 · Clients never write to Firestore.**
Rules deny all client writes, including admin. Every mutation goes through the Python API so
validation, rate limiting and audit logging can't be bypassed.
→ [ADR 0007](./docs/adr/0007-deny-all-client-writes.md)

**4 · The Admin SDK is server-only.**
Every file touching it starts with `import "server-only"`. Without that guard the failure mode is a
leaked credential, not a build error.

**5 · `"use client"` goes as deep in the tree as possible.**
A client `<ThemeToggle>` inside a server `<Nav>`, never a client `<Nav>`. One misplaced directive
pulls the whole subtree into the browser bundle.

**6 · Domains and subdomains are isolated; layering is one-way.**
`backend/functions/src/<domain>/<subdomain>/` — each subdomain does one job, deploys as its own
function (`api_<domain>_<sub>`) and owns all its files: `main.py` (the Firebase function),
`routes.py` (HTTP only), `schemas.py`, `service.py` (rules, no HTTP), `repository.py` (the only
Firestore SDK user; `inbox/contact/rate_limit.py`'s transaction is the one exception). Domains never
import each other, subdomains never import siblings, and there is **no `common/` folder**.
`kernel/` holds only domain-free infrastructure (HTTP adapter, auth, `AuditWriter`, the `kernel.crud`
base classes); `shared/generated` holds the models. Tests live only in `backend/functions/tests/`;
there are no `__init__.py` files outside `shared/generated`.
Read [backend/functions/README.md](./backend/functions/README.md) before backend work.
→ [ADR 0017](./docs/adr/0017-bounded-context-domains.md)

**A content subdomain subclasses the CRUD base.** Its repository extends
`kernel.crud.repository.BaseRepository`, its service extends `kernel.crud.service.CrudService`
(audit trail, publish/unpublish transitions, RFC 7386 merge-patch, reorder), and its routes are
written out — copy `src/content/skills/`. Add only what's specific (`ProjectService.duplicate`).

**7 · Architectural changes get an ADR.**
Anything a stranger would ask "why is it like this?" about. Copy `docs/adr/TEMPLATE.md`, add an
index row, commit it with the change. ADRs are immutable — supersede, never edit.

---

## Conventions

**Optional fields render conditionally.** The project model is ~6 required fields and ~30 optional
ones. A section appears only when its data exists — no empty headings, no `null` placeholders, no
"coming soon". This applies to the public page and the admin form alike.
→ [ADR 0008](./docs/adr/0008-projects-drop-start-end-dates.md)

**Confidential data is stripped server-side.** `client.confidential: true` means the name and logo
must never reach the browser. Filter it in `lib/data/`, not in a component — component-level filtering still
ships the value in the RSC payload.

**Every content collection has `visibility` and `order`.** Public queries filter
`visibility == "public"` and sort by `order`. `unlisted` projects are served at their own URL
(with `noindex`) but never listed or put in the sitemap.

**Admin saves send a real merge patch.** Build it with `lib/merge-patch.ts`'s `toMergePatch`
(original vs. edited) — sending form values directly can't clear a field, because a cleared
field is `undefined` and `JSON.stringify` drops it.

**Timestamps** are ISO strings in schemas, Firestore `Timestamp` in the database. Conversion happens
in the repository layer, in exactly one place.

**Secrets** live in Secret Manager, injected by Terraform. Never in `.env` files, never in git.
`NEXT_PUBLIC_*` Firebase config is public by design — the security is in the rules, not in hiding it.
If a real secret ever genuinely needs to touch disk (a local scratch value, a one-off credential),
it goes in `.secret.local` (or `.secrets.local` / `*.secret.local`) — gitignored, never committed,
never pasted into a doc or commit message. Prefer not writing it to disk at all when a command can
take it piped or as an env var instead.

## Gotchas

- **System Python may be 3.9** (macOS). The Makefile asks `uv python find 3.13`; override with
  `make PYTHON=...` if that finds nothing, or `uv` silently builds against 3.9 and it fails at
  deploy time.
- **Firebase resources need the `google-beta` provider.** A 404 on the standard provider usually
  means this, not a bug.
- **Firestore composite queries need composite indexes.** Generated from `x-firestore.indexes` —
  add the index when you add the query.
- **Cold starts scale with top-level imports.** The root `main.py` imports only the subdomain
  `FUNCTION_TARGET` names; keep each subdomain's imports to what it uses.
- **A new subdomain needs four registrations**: its domain's `FUNCTIONS` table
  (`src/<domain>/main.py`), the `ROUTES` rewrite in `frontend/next.config.ts` (App Hosting has no
  rewrites of its own), the import-linter contracts in `backend/functions/pyproject.toml`, and
  `http_functions` in `infra/terraform/modules/functions`. Each failure is silent in production;
  `tests/test_domain_registry.py` fails `make test` instead.
- **A secret bound in a decorator must have a version before deploy.** `secrets=[...]` on
  `make_function` / a trigger makes `firebase deploy` reject the function otherwise. The contact
  domain binds `TURNSTILE_SECRET_KEY`, `CONTACT_EMAIL_TO` and `RESEND_API_KEY`, and fails closed
  in production without Turnstile — see docs/RUNBOOK.md (Contact form keys).
- **Never construct `a2wsgi.ASGIMiddleware` directly.** It starts a persistent background thread
  at construction time, and Werkzeug's dev-server reloader (which `functions-framework` uses
  locally) forks — the child inherits a dead copy of that thread, and every request hangs forever.
  Reproduced directly with `os.fork()`. Use `kernel/wsgi_bridge.py` (`wsgi_from_asgi`), which drives
  each request with a fresh `asyncio.run()` instead. See ADR 0003's implementation note.
- **Firebase's own tooling needs `backend/functions/requirements.txt` and a stdlib `venv/`**,
  separate from the `uv`-managed `.venv/` used for lint/test — `make setup-backend` generates both.
  Without them, `firebase deploy` and `firebase emulators:start` cannot detect the runtime or load
  any function at all.
- **A `TestClient` call proves the FastAPI app works, not that the Firebase adapter does.** The
  a2wsgi bug above type-checked cleanly and passed every unit test; it only appeared against the
  real emulator. Phase 3's "deploy `make_function()` to the emulator before building further
  domains" step exists for exactly this gap.
- **Every Firebase function — HTTP, trigger or scheduled — must be listed in its domain's
  `FUNCTIONS` table.** Deploy discovery only sees what the root `main.py` exposes; a function defined
  in a subdomain's `main.py` but not listed silently never deploys. `tests/test_main_entrypoint.py`
  cross-checks every function defined in `src/*/*/main.py` against the tables.
- **Emulator-backed tests need no `gcloud` login** — `tests/conftest.py` gives the Admin SDK
  anonymous credentials. Without the emulator they skip.
- **Localhost Lighthouse scores lie.** Only production numbers count.
- **Debug a function directly via `functions-framework`, never through
  `firebase emulators:start --only functions`.** Breakpoints don't reliably hit through that
  emulator's own per-function subprocess model. VS Code configs for this are committed in
  `.vscode/` — see [docs/RUNBOOK.md](./docs/RUNBOOK.md#debugging-vs-code).

## Working style

- Read the relevant `docs/plan/phases/` doc before starting a phase — each has prerequisites, a
  definition of done, and a gotchas list written in advance.
- Tick the checkboxes as work completes; update the status table in `docs/plan/README.md`.
- Prefer finishing a phase to starting the next one.
- When a plan doc turns out to be wrong, fix the doc in the same commit as the code.
