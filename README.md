# nikunjramani.in

Source for my personal site — portfolio, projects and writing.
Live at **[nikunjramani.in](https://nikunjramani.in)** *(not deployed yet)*.

> 📋 Full architecture and build plan: **[PLAN.md](./PLAN.md)**

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16 (App Router) · TypeScript · Tailwind v4 · shadcn/ui |
| Backend | Python 3.13 · FastAPI on Cloud Functions for Firebase (2nd gen) |
| Data | Cloud Firestore · Firebase Storage · Firebase Auth |
| Hosting | Firebase App Hosting |
| Infra | Terraform (`google` / `google-beta`) |
| CI/CD | GitHub Actions + Workload Identity Federation |

Public pages are server-rendered from Firestore, so the site is real HTML for crawlers.
Python owns every write; nothing on the read path can cold-start.

## Layout

```
architecture/   JSON Schemas — the single source of truth for every model
frontend/       Next.js app (public site + /admin)
backend/        Python Firebase Functions (API, triggers, scheduled jobs)
infra/          Terraform for Firebase/GCP + security rules
docs/           Content, design decisions, runbook, ADRs
```

### Schema-first

Models are **generated, never hand-written**. One JSON Schema in `architecture/schemas/`
produces the Pydantic models, the TypeScript types, the Zod validators and the admin form
fields. Add a field once, and it appears everywhere.

```bash
make gen     # regenerate all targets
```

`frontend/src/generated/` and `backend/functions/generated/` are committed but never edited
by hand — CI regenerates and fails on any diff.

## Getting started

> Scaffolding lands in Phase 0 — these commands don't exist yet.

```bash
make setup   # install frontend + backend deps
make dev     # Next.js + Firebase emulators
make gen     # regenerate models from architecture/schemas
make test    # frontend + backend test suites
make deploy  # terraform apply + deploy functions
```

**Prerequisites:** Node 22+, Python 3.13, Terraform 1.9+, Firebase CLI, gcloud CLI.

## Status

Pre-development. See [PLAN.md](./PLAN.md) for the phase breakdown.

- [x] Architecture and build plan
- [ ] Phase 0 — Foundation & infra
- [ ] Phase 1 — Schemas & codegen
- [ ] Phase 2 — Content & design
- [ ] Phase 3 — Backend
- [ ] Phase 4 — Public site
- [ ] Phase 5 — Admin panel
- [ ] Phase 6 — Deploy & DNS
- [ ] Phase 7 — CI/CD

## License

Code is MIT. Site content, copy and images are © Nikunj Ramani — please don't reuse those.
