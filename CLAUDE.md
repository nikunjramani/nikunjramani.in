# CLAUDE.md

Context for working on this repository. Start here; the detail loads from `.claude/` as needed.

## What this is

The personal website at **nikunjramani.in** — portfolio, projects, writing. A server-rendered
Next.js site whose content lives in Firestore, edited through an admin panel on the site itself,
with a Python API (one FastAPI service on Cloud Run) owning every read and write.

**This repository is public.** Never commit secrets, credentials, personal contact details,
employer names, client names, or anything from a private engagement. Reach for a placeholder and
say so. (`.claude/rules/security.md`)

**Status:** Phases 0, 1, 3, 4 and 5 are implemented; Phase 6 is live at `https://nikunjramani.in`
with a few launch checks open; Phase 7 CI/CD is live — PR checks, staging previews, and prod
deploys on merge (since 2026-10-16). Phase 9: the backend runs as one Cloud Run service (2026-10-21). Phase 2: the Technical design is built (`.docs/DESIGN.md`). Backend: 241 tests (76
need the Firestore emulator). Full plan: [`.docs/plan/`](./.docs/plan/README.md).

## Where things are

| Need | Go to |
|---|---|
| How any request / edit / deploy flows, file by file | [`.docs/CODE_FLOW.md`](./.docs/CODE_FLOW.md) |
| Why a piece of code is written this way | [`.docs/decisions/`](./.docs/decisions/README.md) |
| Architecture decisions | [`.docs/adr/`](./.docs/adr/README.md) |
| Operating it (CI/CD, deploy, rollback, secrets) | [`.docs/RUNBOOK.md`](./.docs/RUNBOOK.md) |
| The public site's design system (tokens, type, structure) | [`.docs/DESIGN.md`](./.docs/DESIGN.md) |
| How to work here (verify, PRs, CI, docs upkeep) | `.claude/rules/workflow.md` — always loaded |
| Mistakes not to repeat | `.claude/rules/lessons-learned.md` — always loaded |
| Area rules (backend, frontend, schemas, infra, CI, docs) | `.claude/rules/*.md` — load with matching files |
| Step-by-step playbooks | `.claude/skills/` — `add-api-endpoint`, `add-page`, `add-schema-field`, `write-adr`, `record-decision`, `pull-request`, `ship`, `update-dependencies`, plus vendored `frontend-design`, `web-design-guidelines`, `react-best-practices`, `firebase-security-rules-auditor` |

## Stack

| | |
|---|---|
| Frontend | Next.js 16 App Router · TypeScript strict · Tailwind v4 · shadcn/ui |
| Backend | Python 3.13 · FastAPI, one service on Cloud Run (ADR 0023) |
| Data | Cloud Firestore · Cloud Storage · Firebase Auth · App Check |
| Hosting | Firebase App Hosting |
| Infra | Terraform (`google` + `google-beta`) — prod `nikunjramani-in`, staging `nikunjramani-in-staging` |

## Layout

```
architecture/   JSON Schemas + api-routes.json — the single source of truth for every model
frontend/       Next.js app: site/ · admin/ · shared/ — two surfaces, two root layouts (ADR 0021)
backend/        the API: apps/api.py · src/<domain>/<subdomain> · kernel/ · shared/generated
infra/          Terraform envs + modules · Firestore rules
.github/        pr.yml · deploy.yml · composite actions
.docs/          code flow · code decisions · ADRs · runbook · build plan
.claude/        rules and skills
```

## Commands

```bash
make setup    # install both sides
make dev      # Firebase emulators + the API on :8000 (reloading) + Next.js
make gen      # regenerate models from architecture/  ← after ANY schema or api-routes edit
make validate # validate schemas + example fixtures
make lint     # eslint + tsc + ruff + mypy --strict + import-linter + terraform fmt
make test     # vitest + pytest
```

Deploys are CI's job: a PR deploys its touched targets to **staging** and comments the URL;
merging to `main` deploys them to **prod** (`deploy.yml`, switch: repo variable
`PROD_DEPLOY_ENABLED`). A PR can never reach prod (ADR 0018, 0019). `make deploy` is break-glass.

---

## The seven rules

Load-bearing. Each has an ADR behind it — read it before proposing a change.

**1 · Never hand-edit generated code.** `frontend/src/generated/` and
`backend/shared/generated/` come from `architecture/`. Edit the schema, run `make gen`.
CI fails on drift. → [ADR 0006](./.docs/adr/0006-json-schema-source-of-truth.md)

**2 · Only the Python API touches the database.** Reads and writes alike: pages read through
`lib/data/*`, which calls each content subdomain's public `GET /public` route. The frontend has no
Firestore SDK (ESLint) and no Firestore role (IAM). → [ADR 0022](./.docs/adr/0022-backend-owns-all-data-access.md)

**3 · Clients never write to Firestore.** Rules deny all client writes, including admin. Every
mutation goes through the Python API so validation, rate limiting and audit logging can't be
bypassed. → [ADR 0007](./.docs/adr/0007-deny-all-client-writes.md)

**4 · The Admin SDK is server-only.** In the frontend it's used for Firebase Auth only (the admin
session cookie). Every file touching it starts with `import "server-only"`. Without that guard the
failure mode is a leaked credential, not a build error.

**5 · `"use client"` goes as deep in the tree as possible.** A client `<ThemeToggle>` inside a
server `<Nav>`, never a client `<Nav>`.

**6 · Domains and subdomains are isolated; layering is one way.**
`backend/src/<domain>/<subdomain>/` does one job, is served at `/api/v1/<domain>/<sub>`, and
owns `routes.py` (+ `events.py` if an event starts it) · `schemas.py` · `service.py` ·
`repository.py`. Domains never import each other, subdomains never import siblings, there is
**no `common/` folder**, no `__init__.py` outside `shared/generated`, and tests live only in
`backend/tests/`. `backend/apps/api.py` mounts them all into the one service and nothing imports
it. Content subdomains subclass `kernel.crud` (copy `src/content/skills/`).
→ [ADR 0017](./.docs/adr/0017-bounded-context-domains.md) · [ADR 0023](./.docs/adr/0023-backend-as-one-cloud-run-service.md) · `.claude/rules/backend.md`

**7 · Architectural changes get an ADR; code-level choices get a decision entry.** Anything a
stranger would ask "why is it like this?" about. ADRs are immutable — supersede, never edit.
→ `write-adr` and `record-decision` skills

---

## Conventions

- **Optional fields render conditionally** — no empty headings, no placeholders, in the public
  page and the admin form alike. → [ADR 0008](./.docs/adr/0008-projects-drop-start-end-dates.md)
- **Confidential data is stripped by the API** (`ProjectService.to_public`), never in a component.
- **Every content collection has `visibility` and `order`.** Public queries filter
  `visibility == "public"` and sort by `order`; `unlisted` is served at its URL with `noindex` but
  never listed.
- **Admin saves send a real merge patch** built with `admin/lib/merge-patch.ts`'s `toMergePatch`.
- **Timestamps** are ISO strings in schemas, Firestore `Timestamp`s in the database, converted in
  exactly one place per side.
- **Secrets** live in Secret Manager, never in `.env` or git. `NEXT_PUBLIC_*` Firebase config is
  public by design. A secret that must touch disk goes in `.secret.local` (gitignored).
- **Versions are looked up live**, never from memory; dependency updates go in one PR.

## Working style

- Read the relevant `.docs/plan/phases/` doc before starting a phase; tick its checkboxes and the
  status table in `.docs/plan/README.md` as work completes.
- Keep `.docs/CODE_FLOW.md`, `.docs/decisions/` and `.claude/` true **in the same PR** as the code.
- Push → watch CI to green → merge (`pull-request` skill). Don't stop at a red run.
