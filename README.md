# nikunjramani.in

Source for my personal site — portfolio, projects and writing.
Live at **[nikunjramani.in](https://nikunjramani.in)**.

> 📋 How it all works: **[.docs/CODE_FLOW.md](./.docs/CODE_FLOW.md)** · every doc: **[.docs/](./.docs/README.md)**

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16 (App Router) · TypeScript · Tailwind v4 · shadcn/ui |
| Backend | Python 3.13 · FastAPI, one service on Cloud Run |
| Data | Cloud Firestore · Cloud Storage · Firebase Auth · App Check |
| Hosting | Firebase App Hosting |
| Infra | Terraform (`google` / `google-beta`) — a prod and a staging project |
| CI/CD | GitHub Actions — path-filtered checks, a staging preview per PR, prod deploy on merge |

Public pages are server-rendered from Firestore, so the site is real HTML for crawlers.
Python owns every write; nothing on the read path can cold-start.

## Layout

```
architecture/   JSON Schemas — the single source of truth for every model
frontend/       Next.js app (public site + /admin)
backend/        the Python API — one FastAPI service (routes, event handlers, jobs)
infra/          Terraform for Firebase/GCP + security rules
.docs/          Code flow, code decisions, ADRs, runbook, build plan
.claude/        Rules and skills for Claude Code
```

### Schema-first

Models are **generated, never hand-written**. One JSON Schema in `architecture/schemas/`
produces the Pydantic models, the TypeScript types, the Zod validators and the admin form
fields. Add a field once, and it appears everywhere.

```bash
make gen     # regenerate all targets
```

`frontend/src/generated/` and `backend/shared/generated/` are committed but never edited
by hand — CI regenerates and fails on any diff.

## Getting started

```bash
make setup     # install frontend + backend deps
make dev       # Next.js + Firebase emulators
make gen       # regenerate models from architecture/schemas
make validate  # validate schemas + example fixtures
make lint      # eslint + ruff + mypy + import-linter
make test      # vitest + pytest
make deploy    # break-glass only — production deploys run in CI on merge to main
```

**Prerequisites:** Node 22+, Python 3.13, Terraform 1.9+, Firebase CLI, gcloud CLI.

## Documentation

| | |
|---|---|
| [.docs/CODE_FLOW.md](./.docs/CODE_FLOW.md) | Every flow — page read, admin edit, contact form, media, codegen, infra, CI/CD — file by file |
| [.docs/decisions/](./.docs/decisions/README.md) | Why the code is written the way it is, per area |
| [.docs/adr/](./.docs/adr/README.md) | Architecture decision records — what was decided and why |
| [.docs/RUNBOOK.md](./.docs/RUNBOOK.md) | Operating it: dev, CI/CD, deploy, rollback, secrets, backups |
| [.docs/plan/](./.docs/plan/README.md) | The build plan — architecture, data model, security, and nine phase docs |
| [CLAUDE.md](./CLAUDE.md) · [.claude/](./.claude/) | Context, rules and skills for Claude Code |

## Status

See the [phase table in .docs/plan/](./.docs/plan/README.md#phases--work-these-in-order) for
current build status — kept in one place so it doesn't drift out of sync with reality.

## License

Code is MIT. Site content, copy and images are © Nikunj Ramani — please don't reuse those.
