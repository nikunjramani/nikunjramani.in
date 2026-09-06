# 00 · Overview

**Site:** nikunjramani.in — personal portfolio and writing
**Owner:** Nikunj Ramani · **Updated:** 2026-09-06

---

## The shape of it

A server-rendered Next.js site whose content lives in Firestore, edited through an admin panel
on the site itself, with a Python API owning every write.

Three principles drive every decision below:

1. **Reads never touch Python.** Next.js Server Components read Firestore directly with the Admin
   SDK and cache at the CDN. A cold-starting function can never slow down a page load.
2. **One source of truth for every field.** JSON Schemas in `architecture/` generate the Pydantic
   models, TypeScript types, Zod validators and admin form fields. Nothing is defined twice.
3. **Content is data, not code.** Adding a project is a form submission, never a deploy.

---

## Architecture

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
| Backend | **Cloud Functions for Firebase**, 2nd gen | `python313` | Verified newest supported runtime |
| API | **FastAPI** per domain, one deployed function each | latest | Pydantic validation + OpenAPI, with per-domain isolation · [ADR 0011](../adr/0011-domain-wise-separate-functions.md) |
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

They're the same infrastructure — 2nd-gen functions *run on* Cloud Run. Choosing Functions means one
toolchain (`firebase deploy`), one project, one billing view, and Firestore/Storage triggers for
free. Nothing is given up. And because the API is a plain FastAPI app behind a thin adapter, moving
it to standalone Cloud Run later is a config change, not a rewrite.

### Why Python owns writes but not reads

A Python function cold-starts in 1–3s. On a contact-form submit that's invisible behind a spinner.
On a page load it would be the difference between a fast site and a slow one. So reads go
Next.js → Firestore directly, and Python handles everything that mutates state — where its
validation, business rules and secret handling actually earn their keep.

---

## Where things live

```
architecture/   JSON Schemas — the single source of truth
frontend/       Next.js app (public site + /admin)
backend/        Python Firebase Functions (API, triggers, scheduled jobs)
infra/          Terraform for Firebase/GCP + security rules
docs/adr/       Architecture decision records — one file per decision
docs/plan/      These documents
docs/           Content, design tokens, runbook
```

Details in [01 · Repo Architecture](./01-repo-architecture.md).

---

**Next:** [01 · Repo Architecture](./01-repo-architecture.md) ·
or jump to [Phase 0](./phases/phase-0-foundation.md) to start building.
