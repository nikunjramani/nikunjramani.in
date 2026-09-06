# nikunjramani.in — Build Plan

> **Status:** Draft for approval · **Date:** 2026-09-06 · **Owner:** Nikunj Ramani
> Nothing has been built yet. Read this, mark decisions in §14, and I'll start Phase 0.

---

## 1. The decision, up front

**Recommendation: build it with a backend — but keep the backend off the critical path.**

You asked whether to go static or backed. For a personal site the honest answer is that a static
site would work. But you want (a) to update projects/skills without redeploying, (b) to actually
use your Python skills, and (c) a contact form. That justifies a backend. The trick is *where* you
put it:

- **Reads** (visitor loads your site) → Flutter talks **straight to Firestore**. No Python in the
  path. Fast, cached, free, and it can't go down because your API is cold-starting.
- **Writes + secrets + SEO** (contact form, admin edits, sitemap, email) → **Python/FastAPI**.
  This is where your Python lives, and nobody waiting on a page load ever hits it.

This gives you a real backend without the classic "my personal site is slow because my free-tier
API sleeps" problem.

### Architecture

```
                        ┌──────────────────────────────┐
   visitor  ─────────▶  │  Firebase Hosting (CDN)      │
                        │  Flutter Web build           │
                        └──────────────┬───────────────┘
                                       │ read-only SDK
                                       ▼
                        ┌──────────────────────────────┐
                        │  Cloud Firestore             │  ◀── public read, no write
                        │  projects · skills · exp     │
                        └──────────────┬───────────────┘
                                       ▲ admin writes
                                       │
   you ─────▶ admin UI ────────────────┤
   visitor ─▶ contact form ───────────▶│
                        ┌──────────────┴───────────────┐
                        │  FastAPI on Cloud Run        │
                        │  (Python 3.13)               │
                        │  · POST /contact  + email    │
                        │  · admin CRUD (auth'd)       │
                        │  · sitemap.xml / SEO pages   │
                        │  · Firebase Storage uploads  │
                        └──────────────────────────────┘
```

---

## 2. One concern you should hear before approving

**Flutter Web is bad for SEO.** This is the single real cost of the stack you picked, and for a
personal site — whose whole job is "a recruiter googles my name and finds me" — it matters.

Flutter 3.47 renders to a `<canvas>` via CanvasKit. The HTML renderer is gone. A crawler that
doesn't execute JS sees an effectively empty page. Google *can* render JS, but it does so on a
delayed second pass and inconsistently; LinkedIn/X/WhatsApp link previews and most other bots
don't render at all. Secondary cost: a Flutter web app ships ~1.5–2.5 MB before first paint.

I'm not going to talk you out of Flutter — you know Dart, the design ceiling is high, and the
mitigations below are genuinely good enough for a personal site. But go in with eyes open:

**Mitigations (all included in the plan):**

| # | Mitigation | Phase |
|---|-----------|-------|
| 1 | Full `<meta>` + Open Graph + Twitter card tags baked into `web/index.html` | 2 |
| 2 | **JSON-LD `Person` + `ItemList` schema** in the HTML head — Google reads this without rendering, and it drives the knowledge panel | 2 |
| 3 | A **static HTML skeleton inside `<body>`** (your name, role, bio, project titles) that Flutter paints over on boot — crawlers and no-JS users see real content | 2 |
| 4 | FastAPI serves **server-rendered HTML mirror pages** at `/p/{slug}` for each project, with `<link rel="canonical">` back to the app route | 5 |
| 5 | `sitemap.xml` + `robots.txt` generated from Firestore by the backend | 5 |
| 6 | Deferred CanvasKit load + skeleton splash so first paint isn't a blank white screen | 3 |

If, after seeing this, SEO ranking is your #1 goal, the alternative is Astro or Next.js (static
HTML, perfect SEO) with the same Firebase + FastAPI backend — the backend plan below is unchanged.
Say the word in §14 and I'll swap the frontend. **Otherwise the plan proceeds with Flutter Web.**

---

## 3. Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | **Flutter 3.47 Web** (Dart 3.13) | Your call; installed and ready |
| Routing | `go_router` | Real URLs (`/projects/foo`), deep links, browser back button |
| State | `flutter_riverpod` | Async data from Firestore maps cleanly onto providers |
| Animation | `flutter_animate` | Declarative, tiny, no boilerplate |
| Fonts | **Bundled locally**, not `google_fonts` | `google_fonts` fetches at runtime = flash of wrong font + a 3rd-party request |
| Backend | **FastAPI** + Uvicorn, **Python 3.13** | Your strong suit. (Note: your system Python is 3.9 — we'll use the Homebrew 3.13 in a venv) |
| Pkg manager | `uv` | Fast, lockfile-based, modern replacement for pip/poetry |
| DB | **Cloud Firestore** | Free tier, real-time, direct SDK read from Flutter |
| Files | **Firebase Storage** | Resume PDF, project screenshots, OG images |
| Auth | **Firebase Auth** (Google sign-in, admin custom claim) | Only you ever log in |
| Hosting (web) | **Firebase Hosting** | Free CDN, free SSL, easy custom domain |
| Hosting (API) | **Cloud Run** | Scales to zero, same GCP project, generous free tier |
| Email | **Resend** (free 3k/mo) | Contact form → your inbox. Simpler than SendGrid |
| CI/CD | GitHub Actions | Push to `main` → deploy both |
| Analytics | Firebase Analytics or Umami | Decide later, Phase 6 |

---

## 4. Repository structure

```
nikunjramani.in/
├── PLAN.md                     ← this file
├── README.md
├── .gitignore
├── .github/workflows/
│   ├── frontend.yml            # build + deploy Flutter → Firebase Hosting
│   └── backend.yml             # build + deploy FastAPI → Cloud Run
│
├── frontend/                   # ── FLUTTER WEB ──────────────────
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app.dart                    # MaterialApp.router, theme wiring
│   │   ├── core/
│   │   │   ├── theme/                  # colors, typography, spacing, motion
│   │   │   ├── router/                 # go_router config
│   │   │   ├── responsive/             # breakpoints, adaptive layout helper
│   │   │   └── constants/
│   │   ├── data/
│   │   │   ├── models/                 # Project, Skill, Experience, Profile…
│   │   │   ├── repositories/           # FirestoreRepository per collection
│   │   │   └── providers/              # Riverpod providers
│   │   ├── features/
│   │   │   ├── home/                   # hero, about, highlights
│   │   │   ├── projects/               # grid + detail page
│   │   │   ├── skills/
│   │   │   ├── experience/
│   │   │   ├── blog/                   # phase 6
│   │   │   ├── contact/
│   │   │   └── admin/                  # phase 5, auth-gated
│   │   └── shared/widgets/             # buttons, cards, section headers, nav
│   ├── assets/{fonts,images,icons}/
│   ├── web/index.html                  # SEO head + static skeleton (§2)
│   └── pubspec.yaml
│
├── backend/                    # ── PYTHON / FASTAPI ─────────────
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py                   # pydantic-settings, env-driven
│   │   ├── api/v1/
│   │   │   ├── contact.py  projects.py  skills.py
│   │   │   ├── experience.py  upload.py  seo.py
│   │   ├── core/
│   │   │   ├── firebase.py             # admin SDK init
│   │   │   ├── security.py             # verify Firebase ID token + admin claim
│   │   │   ├── rate_limit.py
│   │   │   └── exceptions.py
│   │   ├── models/                     # pydantic schemas (source of truth)
│   │   ├── services/                   # firestore_service, email_service, storage_service
│   │   └── templates/                  # Jinja2 SEO mirror pages
│   ├── scripts/
│   │   ├── seed_content.py             # push your initial content into Firestore
│   │   ├── set_admin_claim.py          # grant yourself admin
│   │   └── export_backup.py            # nightly Firestore → JSON
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .env.example
│
├── infra/                      # ── FIREBASE / GCP ───────────────
│   ├── firebase.json
│   ├── firestore.rules
│   ├── firestore.indexes.json
│   ├── storage.rules
│   └── deploy.sh
│
└── docs/
    ├── CONTENT.md              # your actual copy, written before we design
    ├── DESIGN.md               # design system decisions
    └── RUNBOOK.md              # deploy, rollback, DNS, secrets
```

---

## 5. Firestore data model

All content lives in Firestore so you can edit without a redeploy. Collections:

### `profile/main` (single doc)
```jsonc
{
  "name": "Nikunj Ramani",
  "headline": "Software Engineer",          // one line under your name
  "tagline": "I build ...",                 // hero sub-line
  "bio": "markdown string",
  "location": "Pune, India",
  "email": "hello@nikunjramani.in",
  "avatarUrl": "...", "ogImageUrl": "...", "resumeUrl": "...",
  "socials": [{ "label": "GitHub", "url": "...", "icon": "github" }],
  "availableForWork": true,
  "updatedAt": "<timestamp>"
}
```

### `projects/{id}`
```jsonc
{
  "slug": "unique-url-safe",              // → /projects/unique-url-safe
  "title": "...", "summary": "1–2 lines for the card",
  "description": "markdown, long form",
  "problem": "...", "solution": "...", "impact": "...",   // the story that matters
  "techStack": ["Python", "FastAPI", "Flutter"],
  "role": "...", "teamSize": 1,
  "coverUrl": "...", "gallery": ["..."],
  "links": { "live": "...", "repo": "...", "caseStudy": "..." },
  "startDate": "2025-01", "endDate": "2025-06",   // null endDate = ongoing
  "featured": true, "published": true, "order": 1
}
```

### `skills/{id}`
```jsonc
{
  "name": "Python", "category": "Backend",   // Backend | Frontend | Cloud | Data | Tools
  "level": 4,                                // 1–5, drives the visual
  "yearsOfExperience": 5, "icon": "python",
  "featured": true, "order": 1
}
```

### `experience/{id}`
```jsonc
{
  "company": "Cybage Software", "role": "...", "employmentType": "Full-time",
  "location": "...", "startDate": "2021-06", "endDate": null,
  "current": true,
  "highlights": ["shipped X, cut Y by Z%"],   // achievements, not duties
  "techStack": ["..."], "logoUrl": "...", "order": 1
}
```

### `education/{id}`, `certifications/{id}`
Standard fields — institution/issuer, title, dates, credential URL, `order`.

### `posts/{id}` — Phase 6, optional
`slug, title, excerpt, contentMd, coverUrl, tags[], readingMinutes, publishedAt, published`

### `contact_messages/{id}` — write-only from the world
`name, email, subject, message, createdAt, ip, userAgent, read, replied, spamScore`

### `site_config/main`
Feature flags + toggles: `showBlog`, `showTestimonials`, `maintenanceMode`, `theme`,
`announcementBanner`.

> **Rule:** every collection carries `published` and `order`. The frontend queries
> `where published == true, orderBy order` — so you can draft content live without it showing.

---

## 6. Security rules

```
// firestore.rules — the whole security posture in one screen
match /databases/{db}/documents {
  function isAdmin() { return request.auth != null && request.auth.token.admin == true; }

  // world reads published content; only admin writes
  match /{col}/{doc} where col in ['profile','projects','skills','experience',
                                   'education','certifications','posts','site_config'] {
    allow read:  if resource.data.published != false;
    allow write: if isAdmin();
  }

  // the world can send you a message but can never read the inbox
  match /contact_messages/{id} {
    allow create: if false;   // ← forced through FastAPI, which rate-limits + spam-checks
    allow read, update, delete: if isAdmin();
  }
}
```
Storage rules: public read on `/public/**`, admin-only write everywhere.

Contact writes are deliberately blocked at the DB and routed through Python — that's your spam
gate. Without it, a bot with your public Firebase config can fill Firestore in an afternoon.

---

## 7. Backend API surface

**Public**
| Method | Path | Notes |
|---|---|---|
| `GET` | `/health` | Cloud Run liveness |
| `POST` | `/api/v1/contact` | Rate-limited 3/hr/IP, honeypot + Turnstile, → Resend email |
| `GET` | `/api/v1/resume` | 302 to signed Storage URL, counts downloads |
| `GET` | `/sitemap.xml`, `/robots.txt` | Generated from Firestore |
| `GET` | `/p/{slug}` | Server-rendered SEO mirror of a project (§2) |

**Admin — requires Firebase ID token with `admin: true`**
| Method | Path |
|---|---|
| `GET/POST/PATCH/DELETE` | `/api/v1/admin/projects[/{id}]` |
| `GET/POST/PATCH/DELETE` | `/api/v1/admin/skills[/{id}]` |
| `GET/POST/PATCH/DELETE` | `/api/v1/admin/experience[/{id}]` |
| `PATCH` | `/api/v1/admin/profile` |
| `POST` | `/api/v1/admin/upload` → signed Storage upload URL |
| `GET/PATCH` | `/api/v1/admin/messages[/{id}]` |
| `POST` | `/api/v1/admin/reorder` — bulk `order` update |

Pydantic models are the contract; FastAPI auto-generates `/docs`. Dart models mirror them.

---

## 8. Frontend pages

| Route | Contents |
|---|---|
| `/` | Hero → About → Featured skills → Featured projects → Experience snapshot → Contact CTA |
| `/projects` | Filterable grid (by tech / category) |
| `/projects/{slug}` | Case study: problem → solution → impact → stack → gallery → links |
| `/about` | Long bio, full skill matrix, education, certifications, résumé download |
| `/experience` | Vertical timeline |
| `/contact` | Form + socials + availability status |
| `/blog`, `/blog/{slug}` | Phase 6, behind `showBlog` flag |
| `/admin/*` | Auth-gated editor, Phase 5 |
| `404` | Custom |

**Design system** (locked in Phase 1, `docs/DESIGN.md`): dark-first with a light toggle, one
accent colour, 8pt spacing scale, 3 breakpoints (mobile <600, tablet 600–1024, desktop >1024),
scroll-reveal + hover motion, WCAG AA contrast, keyboard-navigable, `prefers-reduced-motion`
respected. I'll present **3 visual directions to choose from** at the start of Phase 3 rather than
picking for you.

---

## 9. Content — the part that actually blocks us

You said you're not sure what to put on it. That's normal, and it's the real bottleneck: design and
code are fast, writing is slow. So Phase 1 is a content phase, and here's exactly what to collect
into `docs/CONTENT.md`. **You don't need it all before we start — but the site can't launch without §9.1–9.5.**

**9.1 Identity (30 min)** — Your name as you want it shown. A one-line headline ("Backend engineer
building X"). A 2-sentence tagline. Where you're based. Whether you're open to work.

**9.2 About (1 hr)** — 3 paragraphs: what you do and what you're good at; how you got here; what
you're into outside work. Written like you talk, not like a résumé.

**9.3 Skills (30 min)** — Every tech you'd defend in an interview, grouped as Backend / Frontend /
Cloud & DevOps / Data / Tools, each rated 1–5. Be honest with the 5s.

**9.4 Experience (1 hr)** — For each role: company, title, dates, and **3 bullets of achievements
with numbers**, not job duties. "Cut API p95 from 800ms to 120ms" beats "worked on APIs".

**9.5 Projects — 3 to 6 (2–3 hrs)** — The centrepiece. For each: title, one-line summary, the
problem, what you built, the measurable impact, the stack, screenshots, and links. **Work projects
count** — describe them without leaking anything confidential to your employer. Side projects,
college projects, and things you built to learn all count too.

**9.6 Assets** — Résumé PDF, a decent headshot, project screenshots, favicon, company/tech logos.

**9.7 Later (not launch-blocking)** — Education, certifications, blog posts, testimonials.

---

## 10. Phases

Estimates are focused working hours, not calendar time.

### Phase 0 — Foundation · ~3h
- [ ] `git init`, repo scaffold, `.gitignore`, README
- [ ] Create Firebase project `nikunjramani-in`; enable Firestore, Storage, Auth, Hosting
- [ ] Enable Blaze billing + **₹500 budget alert** (see §12 — real cost is ~₹0, but Storage and Cloud Run require billing enabled)
- [ ] `flutter create` in `frontend/`, deps installed, boots on `flutter run -d chrome`
- [ ] FastAPI skeleton in `backend/` with `uv`, `/health` responding locally
- [ ] Firestore + Storage rules written and deployed
- [ ] Grant yourself the admin claim (`scripts/set_admin_claim.py`)
- **Done when:** both apps run locally and the Firebase project is live.

### Phase 1 — Content + design direction · ~4h (mostly you)
- [ ] You fill in `docs/CONTENT.md` §9.1–9.5
- [ ] I present 3 visual directions; you pick one
- [ ] Design system locked into `docs/DESIGN.md` and coded as Flutter theme
- **Done when:** real copy exists and the palette/type/spacing are decided.

### Phase 2 — Data layer + SEO shell · ~5h
- [ ] Pydantic models ↔ Dart models, generated and matching
- [ ] Firestore repositories + Riverpod providers, loading/error/empty states
- [ ] `seed_content.py` pushes your real content up
- [ ] `web/index.html`: meta, OG, Twitter, JSON-LD, static skeleton (§2 items 1–3)
- **Done when:** your real content is in Firestore and readable from Flutter.

### Phase 3 — Frontend build · ~16h
- [ ] Shared shell: nav, footer, page transitions, theme toggle
- [ ] Home (hero → about → skills → featured projects → experience → CTA)
- [ ] Projects grid + filters, project detail page
- [ ] About, Experience, Contact, 404
- [ ] Responsive pass at all 3 breakpoints; a11y pass; loading skeletons
- **Done when:** every page renders real data and looks right on a phone.

### Phase 4 — Backend build · ~8h
- [ ] Contact endpoint: validation, rate limit, honeypot, Turnstile, Resend email
- [ ] Admin CRUD routers + Firebase token auth dependency
- [ ] Signed-URL upload endpoint
- [ ] pytest suite, ruff + black, Dockerfile
- **Done when:** contact form delivers to your inbox and `/docs` shows a clean API.

### Phase 5 — Deploy · ~5h
- [ ] Deploy Flutter → Firebase Hosting; FastAPI → Cloud Run
- [ ] **GoDaddy DNS → Firebase** (§11); `api.nikunjramani.in` → Cloud Run
- [ ] SEO mirror pages + `sitemap.xml`; submit to Google Search Console
- [ ] GitHub Actions: push to `main` deploys both
- [ ] Lighthouse pass; OG preview tested on LinkedIn/WhatsApp
- **Done when:** https://nikunjramani.in is live with a valid cert. **← LAUNCH**

### Phase 6 — After launch (optional, pick what you want)
Admin editor UI · Blog with markdown rendering · Analytics dashboard · Testimonials ·
Dynamic OG image generation · Nightly Firestore backup job · Dark/light polish · i18n

**Total to launch: ~40h of build + ~4h of your writing.**

---

## 11. Domain setup (GoDaddy → Firebase)

1. Firebase Console → Hosting → **Add custom domain** → `nikunjramani.in`, and again for `www`.
2. Firebase gives you a **TXT** record for ownership and **two A records**. Use exactly what the
   console shows — don't copy IPs from a blog post, they change.
3. GoDaddy → My Products → Domain → **DNS → Manage Zones**:
   - `TXT` `@` → *(verification value from Firebase)*
   - `A` `@` → *(Firebase IP #1)*, TTL 600
   - `A` `@` → *(Firebase IP #2)*, TTL 600
   - `CNAME` `www` → `nikunjramani.in`
   - `CNAME` `api` → *(Cloud Run domain mapping target)*
4. Delete GoDaddy's default parking/forwarding records or they'll fight yours.
5. Wait for propagation (usually <1h, allow 48h). Firebase provisions SSL automatically.
6. **Email** (optional): `hello@nikunjramani.in` via Zoho Mail free tier or Cloudflare Email
   Routing — both free, both need MX records here.

---

## 12. Cost

| Service | Free tier | Our expected use | Cost |
|---|---|---|---|
| Firebase Hosting | 10 GB storage, 360 MB/day transfer | Way under | ₹0 |
| Firestore | 50k reads, 20k writes, 1 GiB/day | Way under | ₹0 |
| Firebase Storage | 5 GB, 1 GB/day download | Way under | ₹0 |
| Firebase Auth | Unlimited for our use | 1 user (you) | ₹0 |
| Cloud Run | 2M requests, 360k GB-s/mo | Way under | ₹0 |
| Resend | 3,000 emails/mo | ~10 | ₹0 |
| Domain | — | Already bought | paid |

**Realistic monthly cost: ₹0.** Two caveats worth knowing:

- Firebase **Storage and Cloud Run require the Blaze (pay-as-you-go) plan** — a card on file even
  though you stay inside the free allowances. That's why Phase 0 sets a **budget alert**.
- Set Firestore/Cloud Run **max-instances = 2** so a runaway loop or a bot can't generate a bill.

---

## 13. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Flutter Web SEO | Recruiters don't find you | §2 — 6 mitigations; Astro fallback available |
| 2 MB initial bundle | Slow first load on mobile data | Deferred loading, skeleton splash, compressed assets, `--wasm` evaluated |
| Public Firebase config abused | Junk data / bill | Strict rules, contact writes forced through API, rate limits, budget cap |
| Contact form spam | Inbox noise | Honeypot + Cloudflare Turnstile + 3/hr IP limit |
| Content never gets written | Site stalls at 90% | Phase 1 is explicitly a content phase with a checklist |
| Cloud Run cold start (~2s) | Slow contact submit | Not on the read path; min-instances=0 is fine, submit shows a spinner |

---

## 14. Decisions I need from you

| # | Question | My recommendation |
|---|---|---|
| 1 | Backend or pure static? | **Backend**, structured as §1 |
| 2 | Flutter Web despite the SEO cost (§2)? | **Yes, proceed** — mitigations are enough for a personal site |
| 3 | Firebase project name | `nikunjramani-in` |
| 4 | Enable Blaze billing with a ₹500 alert? | **Yes** — required for Storage + Cloud Run, real cost ₹0 |
| 5 | Blog at launch? | **No** — Phase 6. Ship without it |
| 6 | Admin UI at launch? | **No** — edit via Firebase Console + seed script until Phase 6 |
| 7 | Dark-first, light toggle? | **Yes** |
| 8 | Contact email destination | `nikunjr@cybage.com` for now, → `hello@nikunjramani.in` later? |
| 9 | GitHub repo: public or private? | **Public** — it's a portfolio piece in itself |
| 10 | Anything in §9 you already have written? | Send it and we skip ahead |

---

## 15. What happens when you approve

I start **Phase 0** immediately: git init, the `frontend/` + `backend/` scaffold, Firebase project
setup instructions for the console steps only you can do, security rules, and both apps booting
locally. Then Phase 1, where I show you 3 design directions and you write §9 content.

Reply with your answers to §14 — or just **"approved, defaults are fine"** and I'll take every
recommendation in the right-hand column and go.
