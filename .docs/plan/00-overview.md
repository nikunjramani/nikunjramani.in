# 00 · Overview

**Site:** nikunjramani.in — personal portfolio and writing
**Owner:** Nikunj Ramani · **Updated:** 2026-09-06

---

## The shape of it

A server-rendered Next.js site whose content lives in Firestore, edited through an admin panel
on the site itself, with a Python API owning every write.

Three principles drive every decision below:

1. **Only the Python API touches the database.** Next.js Server Components read through each
   content function's public `GET /public` route; admin reads and every write go through the same
   API. One codebase knows the database (ADR 0022, which superseded the original
   "reads never touch Python" principle, ADR 0005).
2. **One source of truth for every field.** JSON Schemas in `architecture/` generate the Pydantic
   models, TypeScript types, Zod validators and admin form fields. Nothing is defined twice.
3. **Content is data, not code.** Adding a project is a form submission, never a deploy.

---

## Architecture

> The original design. Since then the backend became one Cloud Run service ([ADR 0023](../adr/0023-backend-as-one-cloud-run-service.md)) and owns reads as well as writes ([ADR 0022](../adr/0022-backend-owns-all-data-access.md)); [CODE_FLOW §1](../CODE_FLOW.md#1--the-system) has the current picture.

```
                    ┌───────────────────────────────────────────┐
  visitor ────────▶ │  Firebase App Hosting                     │
                    │  Next.js 16 · Server Components           │
                    │  → real HTML, ISR-cached at the CDN       │
                    └──────────────┬────────────────────────────┘
                                   │ Admin SDK, server-side only
                                   ▼
                    ┌───────────────────────────────────────────┐
                    │  Cloud Firestore                          │
                    │  projects · skills · experience · posts   │
                    └────────▲──────────────────────┬───────────┘
                             │ writes               │ triggers
                             │                      ▼
  you ─▶ /admin ─ ID token ─▶┌──────────────────────────────────┐
  visitor ─▶ contact form ──▶│  Firebase Functions · Python 3.13│
       via Hosting rewrites  │  one function per domain         │
                             │                                  │
                             │  api_contact   api_projects      │
                             │  api_media     api_skills        │
                             │  api_messages  api_experience    │
                             │  api_settings  api_profile  …    │
                             │                                  │
                             │  triggers:  on_contact_created   │
                             │             on_media_uploaded    │
                             │             on_content_published │
                             │  scheduled: nightly_backup       │
                             └──────────────────────────────────┘

              ┌───────────────────────────────────────────────┐
              │  architecture/*.schema.json  ← SOURCE OF TRUTH│
              │        ├─▶ Pydantic v2 models   (backend)     │
              │        ├─▶ TypeScript types     (frontend)    │
              │        ├─▶ Zod validators       (admin forms) │
              │        └─▶ Firestore rules assertions         │
              └───────────────────────────────────────────────┘
```

---

## Stack

| Layer | Choice | Version | Why |
|---|---|---|---|
| Framework | **Next.js**, App Router | 16.3.x | SSR/SSG = real HTML = SEO. Native on App Hosting |
| Language (FE) | **TypeScript** | 5.x, strict | Types generated from the schemas |
| Styling | **Tailwind CSS** | v4 | Fast; no stylesheet to maintain |
| Components | **shadcn/ui** + Radix | latest | Accessible primitives you own and restyle |
| Animation | **Motion** (ex Framer Motion) | latest | Scroll reveals, page transitions |
| Forms | **react-hook-form** + **Zod** | latest | Zod schemas are generated |
| Icons | **lucide-react** | latest | |
| Backend | **Cloud Run**, one service (Cloud Functions for Firebase until [ADR 0023](../adr/0023-backend-as-one-cloud-run-service.md)) | Python 3.13 | One container image, uvicorn |
| API | **FastAPI**, one app; domains isolated in the code | latest | Pydantic validation + OpenAPI · [ADR 0017](../adr/0017-bounded-context-domains.md), [ADR 0023](../adr/0023-backend-as-one-cloud-run-service.md) |
| Pkg manager (py) | **uv** | latest | Fast, lockfile-based |
| Lint (py) | **ruff** + **mypy --strict** | latest | |
| DB | **Cloud Firestore** | | |
| Files | **Firebase Storage** | | |
| Auth | **Firebase Auth**, Google + `admin` claim | | Only you sign in |
| Hosting | **Firebase App Hosting** | GA | Git-based Next.js SSR deploys |
| IaC | **Terraform** `google` / `google-beta` | 1.9+ | |
| Email | **Resend** | free 3k/mo | |
| CI | **GitHub Actions** + Workload Identity Federation | | No long-lived keys |

> **No monorepo tooling.** A root `Makefile` (`make dev`, `make gen`, `make deploy`) is enough.
> Turborepo or pnpm workspaces would be ceremony for a two-app repo.

---

## Why these choices

### Why not Flutter Web (the original plan)

Flutter 3.47 renders to a `<canvas>` — the HTML renderer was removed. Crawlers that don't execute
JS see an empty page, and LinkedIn/WhatsApp link previews get nothing at all. For a site whose
entire job is "a recruiter googles my name and finds me", that's fatal. Next.js emits real HTML on
the server, which solves it outright. It's also the most transferable frontend skill available.

### Why Firebase Functions rather than Cloud Run

> **Since 2026-10-21 ([ADR 0023](../adr/0023-backend-as-one-cloud-run-service.md)):** the backend is one FastAPI service on Cloud Run, not one Cloud Function per subdomain; triggers are Eventarc and Cloud Scheduler calls to `/internal/*` routes on it. This section describes the original Functions design — [CODE_FLOW](../CODE_FLOW.md) and [backend/README.md](../../backend/README.md) describe what runs now.

They're the same infrastructure — 2nd-gen functions *run on* Cloud Run. Choosing Functions means one
toolchain (`firebase deploy`), one project, one billing view, and Firestore/Storage triggers for
free. Nothing is given up. And because the API is a plain FastAPI app behind a thin adapter, moving
it to standalone Cloud Run later is a config change, not a rewrite.

### Why Python owns writes but not reads

> Superseded by [ADR 0022](../adr/0022-backend-owns-all-data-access.md): the API owns reads too.

A Python function cold-starts in 1–3s. On a contact-form submit that's invisible behind a spinner.
On a page load it would be the difference between a fast site and a slow one. So reads go
Next.js → Firestore directly, and Python handles everything that mutates state — where its
validation, business rules and secret handling actually earn their keep.

---

## Where things live

```
architecture/   JSON Schemas — the single source of truth
frontend/       Next.js app (public site + /admin)
backend/        the Python API — one FastAPI service on Cloud Run (routes, event handlers, jobs)
infra/          Terraform for Firebase/GCP + security rules
.docs/adr/       Architecture decision records — one file per decision
.docs/plan/      These documents
.docs/          Content, design tokens, runbook
```

Details in [01 · Repo Architecture](./01-repo-architecture.md).

---

**Next:** [01 · Repo Architecture](./01-repo-architecture.md) ·
or jump to [Phase 0](./phases/phase-0-foundation.md) to start building.
