# nikunjramani.in — Build Plan (v2)

> **Status:** Draft for approval · **Updated:** 2026-09-06 · **Owner:** Nikunj Ramani
> v2 supersedes v1. Changes: Flutter dropped → Next.js · Cloud Run → Firebase Functions ·
> schema-first `architecture/` folder · Terraform `infra/` folder · admin panel now launch scope ·
> much richer project model. Read, mark decisions in §16, and I'll start Phase 0.

---

## 1. What changed from v1, and why

| # | You said | Decision |
|---|---|---|
| 1 | "use firebase functions for apis" | ✅ Python 3.13 on **Cloud Functions for Firebase (2nd gen)**. Note these *are* Cloud Run underneath — same infra, managed by the Firebase toolchain instead of separately. You lose nothing. |
| 2 | "drop flutter web if its bad for seo, choose whatever is best, i will learn it" | ✅ **Next.js 16 (App Router) + TypeScript**. Server-rendered HTML = perfect SEO, which was the whole problem with Flutter. |
| 3 | "use latest python versions" | ✅ **Python 3.13** — verified as supported *and the default runtime* for Firebase Functions. |
| 4 | "proper architecture, cicd later so keep it in mind" | ✅ Layered structure both sides + §13 CI/CD designed now, wired in Phase 7. |
| 5 | "project details too little, start/end dates make no sense, more fields, optional so it shows only if added" | ✅ Rebuilt in §6 — story blocks, outcomes with metrics, flexible timeline, ~10 optional sections that render only when filled. |
| 6 | "architecture folder with json schema, generate models from there" | ✅ **This is the best idea in your list** and it becomes the keystone of the build. §5. |
| 7 | "terraform folder for firebase/gcp security" | ✅ `infra/terraform/` — §8. |
| 8 | "admin should login on the site and edit everything" | ✅ `/admin` in the site itself, Google sign-in + admin claim. Promoted to **launch scope**. §10. |

### Why Next.js is the right replacement

You need to be found on Google. Next.js renders real HTML on the server, so crawlers, LinkedIn
previews and WhatsApp cards all see actual content — the exact thing Flutter's canvas couldn't do.
It also has first-class **Firebase App Hosting** support (GA since April 2025) so we stay entirely
inside Firebase, and it's the single most employable frontend skill you could pick up. The learning
curve is real but React + TypeScript will serve you far beyond this site.

### Architecture

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
                             │  api          FastAPI, all CRUD  │
                             │  on_contact   → email you        │
                             │  on_upload    → thumbs + OG img  │
                             │  nightly      → Firestore backup │
                             │  revalidate   → bust Next cache  │
                             └──────────────────────────────────┘

              ┌───────────────────────────────────────────────┐
              │  architecture/*.schema.json  ← SOURCE OF TRUTH│
              │        ├─▶ Pydantic v2 models   (backend)     │
              │        ├─▶ TypeScript types     (frontend)    │
              │        ├─▶ Zod validators       (admin forms) │
              │        └─▶ Firestore rules assertions         │
              └───────────────────────────────────────────────┘
```

**Reads never touch Python.** Next.js Server Components read Firestore directly with the Admin SDK
and cache the result at the CDN. Python owns every write. Nobody waiting on a page load ever waits
on a cold start.

---

## 2. Stack

| Layer | Choice | Version | Why |
|---|---|---|---|
| Framework | **Next.js**, App Router | 16.3.x | SSR/SSG = real HTML = SEO. App Hosting native |
| Language (FE) | **TypeScript** | 5.x, strict | Types generated from your schemas |
| Styling | **Tailwind CSS** | v4 | Fast, no CSS files to maintain |
| Components | **shadcn/ui** + Radix | latest | Accessible primitives you own and can restyle |
| Animation | **Motion** (ex Framer Motion) | latest | Scroll reveals, page transitions |
| Forms | **react-hook-form** + **Zod** | latest | Zod schemas generated from JSON Schema |
| Icons | **lucide-react** | latest | |
| Content | **MDX** (blog, phase 8) | | |
| Backend | **Cloud Functions for Firebase, 2nd gen** | `python313` | Your ask; verified newest runtime |
| API | **FastAPI** via `a2wsgi` in one HTTP function | latest | Pydantic validation + free OpenAPI docs, and portable to plain Cloud Run later |
| Pkg manager (py) | **uv** | latest | Fast, lockfile-based |
| Lint/format (py) | **ruff** + **mypy --strict** | latest | |
| DB | **Cloud Firestore** | | |
| Files | **Firebase Storage** | | |
| Auth | **Firebase Auth**, Google provider + `admin` claim | | Only you log in |
| Hosting | **Firebase App Hosting** | GA | Git-based Next.js SSR deploys — half our CI/CD for free |
| IaC | **Terraform** + `google` / `google-beta` | | §8 |
| Email | **Resend** | free 3k/mo | |
| CI | **GitHub Actions** + Workload Identity Federation | | No long-lived keys |

> Monorepo tooling: deliberately **none**. A `Makefile` at the root (`make dev`, `make gen`,
> `make deploy`) is enough. Turborepo/pnpm workspaces would be ceremony for a two-app repo.

---

## 3. Repository structure

```
nikunjramani.in/
├── PLAN.md · README.md · Makefile · .gitignore · .editorconfig
│
├── architecture/                 # ══ SOURCE OF TRUTH — §5 ══
│   ├── schemas/                  # JSON Schema draft 2020-12
│   ├── enums/  examples/  codegen/  docs/
│   └── VERSIONING.md
│
├── frontend/                     # ══ NEXT.JS 16 ══
│   ├── src/
│   │   ├── app/
│   │   │   ├── (site)/                    # public, server-rendered
│   │   │   │   ├── page.tsx               # /
│   │   │   │   ├── projects/page.tsx
│   │   │   │   ├── projects/[slug]/page.tsx
│   │   │   │   ├── about/  experience/  contact/  blog/
│   │   │   │   └── layout.tsx             # nav + footer
│   │   │   ├── (admin)/admin/             # private, client-side — §10
│   │   │   │   ├── layout.tsx             # auth guard
│   │   │   │   ├── page.tsx               # dashboard
│   │   │   │   ├── projects/[id]/page.tsx
│   │   │   │   ├── skills/  experience/  media/  messages/  settings/
│   │   │   ├── api/revalidate/route.ts    # on-demand ISR bust
│   │   │   ├── sitemap.ts  robots.ts  opengraph-image.tsx
│   │   │   └── layout.tsx  not-found.tsx
│   │   ├── components/
│   │   │   ├── ui/                        # shadcn primitives
│   │   │   ├── site/                      # Hero, ProjectCard, Timeline, SkillGrid…
│   │   │   ├── admin/                     # SchemaForm, MediaPicker, ReorderList…
│   │   │   └── seo/                       # JsonLd, MetaTags
│   │   ├── lib/
│   │   │   ├── firebase/{admin.ts,client.ts,auth.ts}
│   │   │   ├── data/                      # one query module per collection
│   │   │   ├── api/                       # typed client for the Python API
│   │   │   └── utils/
│   │   ├── generated/                     # ⚠ codegen output — never hand-edit
│   │   │   ├── types.ts  schemas.zod.ts
│   │   ├── hooks/  styles/  config/
│   ├── public/
│   ├── next.config.ts  tailwind.config.ts  tsconfig.json
│   └── apphosting.yaml                    # App Hosting build + env config
│
├── backend/                      # ══ PYTHON 3.13 FUNCTIONS ══
│   └── functions/
│       ├── main.py                        # entrypoint: exports every function
│       ├── api/
│       │   ├── app.py                     # FastAPI app factory
│       │   ├── deps.py                    # auth, pagination, rate-limit deps
│       │   └── routers/
│       │       ├── public/{contact,resume,health}.py
│       │       └── admin/{projects,skills,experience,education,
│       │                  certifications,posts,profile,media,
│       │                  messages,settings}.py
│       ├── triggers/
│       │   ├── on_contact_created.py      # → Resend email + spam score
│       │   ├── on_media_uploaded.py       # → WebP + thumbnails + blurhash
│       │   └── on_content_published.py    # → revalidate Next.js cache
│       ├── scheduled/
│       │   ├── nightly_backup.py          # Firestore → Storage JSON
│       │   └── weekly_digest.py           # optional
│       ├── core/
│       │   ├── config.py                  # pydantic-settings
│       │   ├── firebase.py  security.py  errors.py  logging.py
│       │   └── rate_limit.py
│       ├── services/                      # firestore, storage, email, image, seo
│       ├── repositories/                  # one per collection, generic base
│       ├── generated/models/              # ⚠ codegen output — never hand-edit
│       ├── tests/{unit,integration}/
│       ├── pyproject.toml  requirements.txt  .env.example
│
├── infra/                        # ══ TERRAFORM — §8 ══
│   ├── terraform/{modules,envs}/
│   ├── rules/{firestore.rules,firestore.indexes.json,storage.rules}
│   └── scripts/bootstrap.sh
│
├── docs/  CONTENT.md · DESIGN.md · RUNBOOK.md · ADR/
└── .github/workflows/            # §13
```

---

## 4. Layering rules (so this stays clean)

**Backend — strict one-way dependency:**
```
router → service → repository → Firestore
   ↑         ↑          ↑
   └── generated Pydantic models (shared by all three)
```
- Routers do HTTP only: parse, authorize, delegate, serialize. No business logic, no Firestore.
- Services hold the rules (slug uniqueness, publish transitions, reordering, cache busting).
- Repositories are the only code that touches the Firestore SDK. A generic `BaseRepository[T]`
  gives every collection CRUD + pagination for free.
- **No hand-written models, ever.** They come from `architecture/`.

**Frontend:**
```
page (server) → lib/data/* → Firebase Admin SDK     ← reads
page (client) → lib/api/*  → Python API             ← writes
```
- Server Components fetch; Client Components only handle interaction. `"use client"` as deep in the
  tree as possible.
- `lib/data/` is the *only* place Firestore is queried. Components never import the SDK.
- Nothing in `(site)/` may import from `(admin)/` — the admin bundle must never ship to visitors.

---

## 5. `architecture/` — schema-first (the keystone)

You were right that this is the correct backbone. One JSON Schema edit propagates to five places,
so backend, frontend, forms, validation and docs can never drift apart.

```
architecture/
├── schemas/
│   ├── common/               # $defs reused everywhere
│   │   ├── link.schema.json          media.schema.json
│   │   ├── richtext.schema.json      timeline.schema.json
│   │   ├── metric.schema.json        seo.schema.json
│   │   └── audit.schema.json         # createdAt/updatedAt/createdBy
│   ├── profile.schema.json           project.schema.json
│   ├── skill.schema.json             experience.schema.json
│   ├── education.schema.json         certification.schema.json
│   ├── post.schema.json              contact-message.schema.json
│   └── site-config.schema.json
├── enums/                    # one file per enum, imported by schemas
│   ├── project-kind.json  project-status.json  skill-category.json
│   ├── link-type.json     visibility.json      media-type.json
├── examples/                 # valid + intentionally-invalid fixtures
├── codegen/
│   ├── generate.sh                   # `make gen`
│   ├── python.yaml                   # datamodel-code-generator → Pydantic v2
│   ├── typescript.json               # json-schema-to-typescript
│   └── zod.mjs                       # json-schema-to-zod → admin forms
├── docs/ERD.md               # generated collection diagram
└── VERSIONING.md
```

### The pipeline

| Target | Tool | Output |
|---|---|---|
| Pydantic v2 models | `datamodel-code-generator` | `backend/functions/generated/models/` |
| TypeScript types | `json-schema-to-typescript` | `frontend/src/generated/types.ts` |
| Zod validators | `json-schema-to-zod` | `frontend/src/generated/schemas.zod.ts` |
| **Admin form fields** | custom renderer reading the schema | forms build themselves — §10 |
| Firestore rules asserts | small script | required-field checks in `firestore.rules` |
| ERD / field docs | script | `architecture/docs/` |

**Rules of the road**
1. `architecture/` is the only place a field is ever defined.
2. `generated/` is committed but never hand-edited — CI runs `make gen` and fails on any diff.
3. Every schema carries `x-firestore` metadata (collection name, indexes, whether public-readable).
4. Every schema is versioned; breaking changes get a migration script in `backend/migrations/`.
5. `examples/` are validated in CI, so the schemas stay honest.

**The payoff:** adding "Podcast link" to projects = edit one JSON file, run `make gen`. The Python
API validates it, TypeScript knows about it, the admin form grows the field, and the detail page can
render it. That's the whole reason to do this.

---

## 6. The project model, rebuilt

You were right — `startDate`/`endDate` was wrong for projects, and the model was thin. New design:
**6 required fields, everything else optional, and the UI renders a section only when you've filled
it in.** An empty project is still a valid project; a fully-filled one is a case study.

```jsonc
{
  // ─── required (6) ───────────────────────────────────────────
  "slug": "realtime-inventory-sync",
  "title": "Realtime Inventory Sync",
  "summary": "One or two lines. This is the card text.",
  "kind": "professional",        // professional | personal | open-source
                                 // academic | freelance | experiment
  "status": "shipped",           // concept | in-progress | shipped
                                 // maintained | archived
  "visibility": "public",        // public | unlisted | draft

  // ─── timeline — replaces start/end dates ────────────────────
  "timeline": {
    "displayLabel": "2025 · 4 months",   // free text; wins over everything
    "year": 2025, "durationMonths": 4, "ongoing": false
  },

  // ─── the story. every block optional, renders if present ────
  "content": {
    "overview":  "richtext",
    "problem":   "what was broken, and who it hurt",
    "approach":  "what you built and why that way",
    "architecture": {
      "description": "...",
      "diagramUrl": "...",
      "components": [{ "name": "Ingest worker", "role": "...", "tech": "Python" }]
    },
    "challenges": [{ "title": "Clock skew across regions", "detail": "..." }],
    "outcomes":   [{ "label": "p95 latency", "before": "800ms",
                     "after": "120ms", "delta": "-85%", "highlight": true }],
    "learnings":  ["..."],
    "futureWork": ["..."]
  },

  // ─── tech ───────────────────────────────────────────────────
  "stack": [{ "name": "FastAPI", "category": "backend", "primary": true }],
  "tags":  ["realtime", "distributed-systems"],

  // ─── context ────────────────────────────────────────────────
  "role":  "Backend lead",
  "team":  { "size": 4, "myScope": "API design + data pipeline" },
  "client":{ "name": "…", "logoUrl": "…", "confidential": true },
           // confidential:true → renders "a logistics client", name never sent to the browser

  // ─── media ──────────────────────────────────────────────────
  "cover":   { "url": "…", "alt": "…", "blurhash": "…", "width": 1600, "height": 900 },
  "gallery": [{ "url": "…", "alt": "…", "caption": "…", "type": "image" }],
  "video":   { "url": "…", "provider": "youtube", "thumbnailUrl": "…" },

  // ─── links: an array, so new kinds need no schema change ────
  "links": [{ "type": "repo", "label": "Source", "url": "…", "primary": true }],
           // live | repo | docs | case-study | demo | paper | store | article | video

  // ─── social proof ───────────────────────────────────────────
  "testimonial": { "quote": "…", "author": "…", "role": "…", "avatarUrl": "…" },
  "metrics":     [{ "label": "monthly users", "value": "12k", "icon": "users" }],
  "awards":      [{ "title": "…", "issuer": "…", "year": 2025, "url": "…" }],
  "collaborators": [{ "name": "…", "role": "…", "url": "…" }],

  // ─── publishing ─────────────────────────────────────────────
  "featured": true, "order": 1, "pinned": false,
  "seo": { "metaTitle": "…", "metaDescription": "…",
           "ogImageUrl": "…", "keywords": ["…"] },
  "readingMinutes": 4,
  "createdAt": "…", "updatedAt": "…", "publishedAt": "…"
}
```

**Progressive disclosure in the UI:** the detail page walks the object and renders only the blocks
that exist. Three filled fields → a clean short page. Twenty → a full case study. No empty headings,
no `null` placeholders. The admin form does the same: core fields up top, the rest in collapsible
"add a section" panels so it never feels like a 40-field wall.

`skill`, `experience` and `education` get the same treatment — a small required core plus optional
extras (`endorsements`, `projectsUsedIn`, `certificationUrl`, `highlights`, `techStack`,
`companyLogo`, `promotions[]`). Full definitions land in `architecture/schemas/` in Phase 1.

---

## 7. Security model

Three layers, each independently sufficient:

1. **Firestore rules** — public gets read on published docs; **client writes are denied entirely**,
   including for you. Everything mutating goes through Python.
2. **API auth** — every `/admin/*` route requires a Firebase ID token with a custom `admin: true`
   claim, verified server-side by the Admin SDK. Signing in is not enough; you must hold the claim.
3. **Next.js middleware** — `/admin/*` checks a session cookie before rendering. Convenience, not
   the real gate.

```
// firestore.rules
function isPublished() { return resource.data.visibility == 'public'; }

match /{col}/{id} where col in ['profile','projects','skills','experience',
                                'education','certifications','posts','site_config'] {
  allow read:  if isPublished();
  allow write: if false;              // ← Python API only, no exceptions
}
match /contact_messages/{id} { allow read, write: if false; }
```

Storage: public read on `/public/**` only; all writes via signed URLs the API issues.
Secrets (Resend key, Turnstile secret) live in **Secret Manager**, injected into functions by
Terraform — never in `.env` files in git.

Contact form defences: honeypot field + Cloudflare Turnstile + 3/hour/IP + body size cap + a spam
score computed in the Firestore trigger.

---

## 8. `infra/` — Terraform

```
infra/terraform/
├── modules/
│   ├── project/       # APIs enabled, labels, budget
│   ├── firestore/     # database, indexes, rules release, TTL policies
│   ├── storage/       # buckets, rules, CORS, lifecycle rules
│   ├── functions/     # 2nd-gen functions, runtime SA, min/max instances
│   ├── app-hosting/   # Next.js backend, GitHub repo link, env vars
│   ├── iam/           # least-privilege service accounts + WIF for GitHub
│   ├── secrets/       # Secret Manager entries + accessor bindings
│   └── monitoring/    # budget alert, uptime check, error-rate alert
├── envs/
│   ├── prod/          # nikunjramani-in
│   └── staging/       # optional, same modules, cheaper knobs
└── backend.tf         # GCS remote state + locking
```

**Being straight about the limits:** Terraform can't do 100% of it. These stay manual, once, ~20 min
in Phase 0 — and I'll script what's scriptable in `infra/scripts/bootstrap.sh`:

- Creating the GCP project + attaching billing
- Adding Firebase to the project (`firebase projects:addfirebase`)
- OAuth consent screen + enabling the Google auth provider
- Authorising the GitHub connection for App Hosting
- The GCS bucket that holds Terraform's own state (chicken-and-egg)

Everything after that is `terraform apply`, reviewable in a PR diff. Firebase resources need the
`google-beta` provider — that's expected, not a workaround.

**Guardrails Terraform will enforce:** functions `max_instances = 3`, a budget alert at ₹500 with a
100% hard notification, uptime check on `/health`, and least-privilege SAs (the functions SA gets
Firestore + Storage + Secret accessor; nothing else).

---

## 9. Public site

| Route | Rendering | Contents |
|---|---|---|
| `/` | ISR 1h | Hero → About → Skills → Featured projects → Experience → CTA |
| `/projects` | ISR 1h | Filterable grid: kind, tech, status |
| `/projects/[slug]` | SSG + on-demand revalidate | The case study — §6 progressive disclosure |
| `/about` | ISR | Long bio, full skill matrix, education, certifications, résumé |
| `/experience` | ISR | Timeline with achievements |
| `/contact` | static | Form → Python API, plus socials + availability |
| `/blog`, `/blog/[slug]` | ISR | Phase 8, behind a flag |
| `/sitemap.xml`, `/robots.txt`, `/og/*` | dynamic | Generated from Firestore |

**SEO, now actually solved:** per-page `generateMetadata`, JSON-LD (`Person`, `WebSite`,
`BreadcrumbList`, `CreativeWork` per project), dynamic OG images via `opengraph-image.tsx`, canonical
URLs, generated sitemap, and a Core Web Vitals budget (LCP < 2.0s, CLS < 0.05, INP < 200ms) checked
by Lighthouse CI.

**Design:** dark-first with a light toggle, one accent colour, 4pt spacing scale, fluid type,
Tailwind v4 tokens, WCAG AA, full keyboard nav, `prefers-reduced-motion` honoured. I'll show you
**3 visual directions** at the start of Phase 4 rather than picking for you.

---

## 10. Admin panel — exactly what you described

Go to `nikunjramani.in/admin`, sign in with Google, edit everything. No console, no redeploy.

| Route | What it does |
|---|---|
| `/admin/login` | Google sign-in; rejects anyone without the `admin` claim |
| `/admin` | Dashboard: content counts, unread messages, recent edits, quick actions |
| `/admin/projects` | Table: search, filter by visibility/kind, **drag to reorder**, duplicate, delete |
| `/admin/projects/[id]` | The big one — §6 editor. Core fields, then collapsible optional sections |
| `/admin/skills` | Inline-editable grid, drag to reorder, category grouping |
| `/admin/experience` · `/education` · `/certifications` | Same pattern |
| `/admin/posts` | MDX editor with live preview (Phase 8) |
| `/admin/profile` | Bio, headline, socials, résumé upload, availability toggle |
| `/admin/media` | Upload, browse, alt text, copy URL, delete. Auto WebP + thumbnails |
| `/admin/messages` | Contact inbox: read/unread, replied, spam, export |
| `/admin/settings` | Feature flags, announcement banner, maintenance mode |

**Schema-driven forms.** The editor doesn't hard-code fields — a `<SchemaForm>` component reads the
JSON Schema and renders the right control per field (text, richtext, array-of-objects, media picker,
enum select), validated by the generated Zod schema. Add a field to `architecture/`, run `make gen`,
and it appears in the form. This is the compounding payoff of your architecture-folder idea.

Also: draft/publish with **preview-before-publish**, autosave to localStorage, optimistic UI,
"unsaved changes" guard, and every write stamped with `updatedAt` + an audit trail.

---

## 11. Content — still the real bottleneck

Design and code are the fast part; writing is slow. Fill `docs/CONTENT.md`:

- **11.1 Identity** (30m) — name, one-line headline, tagline, location, open-to-work?
- **11.2 About** (1h) — 3 paragraphs: what you're good at · how you got here · who you are outside work
- **11.3 Skills** (30m) — everything you'd defend in an interview, grouped, rated 1–5. Be honest with the 5s
- **11.4 Experience** (1h) — per role: 3 bullets of **achievements with numbers**, not duties
- **11.5 Projects, 3–6** (2–3h) — the centrepiece. Use §6 as the questionnaire: problem, approach, outcomes with real metrics, stack, screenshots, links. Work projects count — set `client.confidential: true` and describe them without naming names
- **11.6 Assets** — résumé PDF, headshot, screenshots, favicon
- **11.7 Later** — education, certifications, blog, testimonials

§11.1–11.5 are launch-blocking. You can start Phase 0–1 before writing a word.

---

## 12. Phases

Focused working hours, not calendar time.

**Phase 0 — Foundation & infra · ~6h**
`git init` · repo skeleton · GCP project + Firebase + billing + budget alert · Terraform state bucket
· `terraform apply` for Firestore, Storage, IAM, Secret Manager · rules deployed · admin claim granted
to your account · Next.js and Functions both booting locally.
→ *Done when `make dev` runs both apps and `terraform plan` is clean.*

**Phase 1 — Architecture & codegen · ~7h**
Every JSON Schema written · enums · examples · `make gen` producing Pydantic + TS + Zod · CI drift check
· ERD generated.
→ *Done when one schema edit updates all three targets with zero hand-editing.*

**Phase 2 — Content & design direction · ~5h (mostly you)**
You write §11.1–11.5 · I present 3 visual directions · design tokens locked into Tailwind ·
`docs/DESIGN.md`.

**Phase 3 — Backend · ~12h**
FastAPI app + `a2wsgi` wrapper · auth dependency · `BaseRepository` + per-collection repos · services ·
all admin CRUD routers · contact endpoint with Turnstile + rate limit · Firestore/Storage/scheduled
triggers · pytest with the emulator suite · ruff + mypy clean.
→ *Done when `/docs` shows the full API and the emulator test suite passes.*

**Phase 4 — Public site · ~16h**
Layout shell · nav/footer · theme toggle · Home · Projects grid + filters · the §6 case-study page ·
About · Experience · Contact · 404 · responsive at 3 breakpoints · a11y pass · SEO metadata + JSON-LD
+ OG images · Lighthouse ≥ 95.

**Phase 5 — Admin panel · ~14h**
Auth guard + middleware · dashboard · `<SchemaForm>` renderer · project editor with optional-section
panels · media library with upload + processing · drag-reorder · messages inbox · settings · preview
before publish.

**Phase 6 — Deploy & DNS · ~5h**
App Hosting backend live · functions deployed · **GoDaddy DNS → Firebase** (§14) · SSL · Search Console
+ sitemap submitted · OG previews verified on LinkedIn/WhatsApp · smoke tests. **← LAUNCH**

**Phase 7 — CI/CD hardening · ~5h**
The workflows in §13, Workload Identity Federation, PR previews, Lighthouse CI, branch protection.

**Phase 8 — After launch**
Blog + MDX · analytics dashboard · testimonials · view counts · RSS · i18n · dark/light polish.

**To launch: ~65h build + ~5h of your writing.**

---

## 13. CI/CD (designed now, wired in Phase 7)

| Workflow | Trigger | Does |
|---|---|---|
| `schemas.yml` | PR touching `architecture/` | Validate schemas, validate examples, `make gen`, **fail on any diff** |
| `ci-frontend.yml` | PR | `tsc --noEmit`, eslint, vitest, `next build`, Lighthouse CI budget |
| `ci-backend.yml` | PR | ruff, `mypy --strict`, pytest against the Firebase emulator |
| `infra-plan.yml` | PR touching `infra/` | `terraform fmt -check`, `validate`, `plan` → posted as a PR comment |
| `deploy.yml` | push to `main` | `terraform apply` → deploy functions → App Hosting auto-builds from git |
| `preview.yml` | PR | App Hosting preview channel + a comment with the URL |
| `backup.yml` | nightly cron | Verify the Firestore export ran |

Auth via **Workload Identity Federation** — no service-account JSON keys in GitHub secrets.
Structure that supports this from day one: independent `frontend/` `backend/` `infra/` roots, path
filters so unrelated changes don't rebuild everything, and `make` targets that CI reuses verbatim.

---

## 14. Domain (GoDaddy → Firebase)

1. App Hosting → Add custom domain → `nikunjramani.in`, then `www`.
2. Use the **exact** TXT + A records the console shows you — never IPs from a blog post.
3. GoDaddy → DNS → Manage Zones: add the TXT, the A records (TTL 600), `CNAME www → nikunjramani.in`.
4. **Delete GoDaddy's default parking/forwarding records** or they will fight yours.
5. Propagation usually < 1h. SSL is automatic.
6. Optional email `hello@nikunjramani.in` — Zoho Mail free tier or Cloudflare Email Routing.

---

## 15. Cost & risk

Everything sits inside free tiers: Firestore 50k reads/day, Storage 5 GB, Functions 2M calls/mo,
App Hosting on Cloud Run's free tier, Resend 3k emails/mo. **Realistic monthly cost: ₹0** — but
Blaze (card on file) is required for Storage, Functions and App Hosting, which is why Phase 0 sets a
₹500 budget alert and caps `max_instances`.

| Risk | Mitigation |
|---|---|
| Next.js/React learning curve | Phases are ordered so you learn on the public site before the harder admin work; I'll comment generously and write `docs/ADR/` for the non-obvious calls |
| Schema churn early on | Versioning + migration scripts from Phase 1; churn is cheap *because* it's centralised |
| Function cold start (~1–3s, Python) | Write path only. Never blocks a page load |
| Terraform partial coverage | §8 lists the manual steps honestly; `bootstrap.sh` scripts what it can |
| Admin panel scope creep | Phase 5 has a fixed route list. Extras go to Phase 8 |
| Content never gets written | Phase 2 is explicitly a content phase with a checklist |

---

## 16. Decisions I need from you

| # | Question | My recommendation |
|---|---|---|
| 1 | Next.js 16 + TypeScript as the frontend? | **Yes** — solves SEO, most transferable skill |
| 2 | FastAPI-inside-one-Function, or many small plain Functions? | **FastAPI in one** — validation + OpenAPI + portable off Firebase later |
| 3 | Firebase project id | `nikunjramani-in` |
| 4 | Staging environment too, or prod only? | **Prod only** now; Terraform modules make staging a 1-day add later |
| 5 | Enable Blaze + ₹500 budget alert? | **Yes** — required; real cost ₹0 |
| 6 | Admin panel at launch (Phase 5)? | **Yes** — you asked for it, and it's what makes the site maintainable |
| 7 | Blog at launch? | **No** — Phase 8 |
| 8 | Contact email destination | `nikunjr@cybage.com` now → `hello@nikunjramani.in` later? |
| 9 | GitHub repo public or private? | **Public** — it's a portfolio piece in itself |
| 10 | Anything from §11 already written? | Send it and we skip ahead |

---

## 17. On approval

I start **Phase 0**: repo skeleton, `Makefile`, Terraform modules, and a checklist of the handful of
console clicks only you can do (§8). Then **Phase 1**, where the schemas get written and the codegen
pipeline goes live — after which every later phase gets faster.

Reply with §16, or just **"approved, defaults are fine"** and I'll take every recommendation in the
right-hand column and go.
