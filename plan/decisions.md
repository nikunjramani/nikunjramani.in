# Decisions

Open questions blocking Phase 0, plus the log of what's already settled and why.

---

## ⏳ Open — needed before Phase 0

| # | Question | Recommendation | Answer |
|---|---|---|---|
| 1 | Next.js 16 + TypeScript as the frontend? | **Yes** — solves SEO, most transferable skill | |
| 2 | FastAPI in one Function, or many small plain Functions? | **FastAPI in one** — validation + OpenAPI + portable off Firebase later | |
| 3 | Firebase project id | `nikunjramani-in` | |
| 4 | Staging environment, or prod only? | **Prod only** — modules make staging a 1-day add later | |
| 5 | Enable Blaze + ₹500 budget alert? | **Yes** — required for Storage/Functions/App Hosting; real cost ₹0 | |
| 6 | Admin panel at launch (Phase 5)? | **Yes** — you asked for it, and it's what makes the site maintainable | |
| 7 | Blog at launch? | **No** — Phase 8 | |
| 8 | Contact email destination | `nikunjr@cybage.com` now → `hello@nikunjramani.in` later | |
| 9 | GitHub repo public or private? | **Public** — it's a portfolio piece in itself | |
| 10 | Anything from [06 · Content](./06-content-checklist.md) already written? | Send it and we skip ahead | |

> Answer these inline in the table, or just say **"approved, defaults are fine"** to take every
> recommendation as written.

---

## ✅ Settled

### D-001 · Next.js instead of Flutter Web
**Date:** 2026-09-06 · **Status:** Accepted

Flutter 3.47 renders to `<canvas>` (the HTML renderer was removed), so crawlers and link-preview
bots see an empty page. For a site whose purpose is being found by name, that's disqualifying.
Next.js Server Components emit real HTML.

*Rejected:* Flutter Web (SEO), Astro (weaker fit once an admin panel is in scope — it's built for
static content, and we need an interactive authenticated app).

*Cost accepted:* a real React/TypeScript learning curve.

### D-002 · Firebase Functions instead of standalone Cloud Run
**Date:** 2026-09-06 · **Status:** Accepted

Requested. Costs nothing to accept: 2nd-gen functions *run on* Cloud Run, so it's the same
infrastructure with one toolchain, one billing view, and Firestore/Storage triggers included.

### D-003 · FastAPI inside a single HTTP function
**Date:** 2026-09-06 · **Status:** Accepted

The Python Functions SDK hands you a Flask request. Wrapping a FastAPI app with `a2wsgi` keeps
Pydantic validation and auto-generated OpenAPI docs, and means the API is portable to plain Cloud
Run later without a rewrite.

*Rejected:* raw Flask (loses Pydantic + OpenAPI), one function per endpoint (no shared routing or
middleware; a dozen deploy units for a personal site).

### D-004 · Python 3.13
**Date:** 2026-09-06 · **Status:** Accepted

Verified: Firebase Functions gen-2 supports Python 3.10–3.13, with **3.13 as the default runtime**.
Note the `manage-functions` docs page still shows only 3.10/3.11 — it's stale; the get-started page
and release notes are correct.

*Local caveat:* system Python is 3.9. We use the Homebrew 3.13 in a venv.

### D-005 · Reads bypass Python entirely
**Date:** 2026-09-06 · **Status:** Accepted

Next.js Server Components read Firestore directly via the Admin SDK. Python owns writes only.
A 1–3s cold start is invisible behind a submit spinner and unacceptable on a page load.

### D-006 · JSON Schema as the single source of truth
**Date:** 2026-09-06 · **Status:** Accepted

Proposed by Nikunj. One schema per collection generates Pydantic models, TypeScript types, Zod
validators, admin form fields and rules assertions. Cost is a day of setup in Phase 1; the payoff is
that every later field change is a one-file edit — and it's what makes the admin panel cheap.

### D-007 · All client writes denied, including admin
**Date:** 2026-09-06 · **Status:** Accepted

Firestore rules deny writes to every client. Everything mutating goes through the API, so
validation, rate limiting, audit logging and business rules can't be bypassed. Cost: one extra hop
on save.

### D-008 · Projects drop start/end dates
**Date:** 2026-09-06 · **Status:** Accepted

Raised by Nikunj as meaningless for projects. Replaced with `timeline.displayLabel` (free text like
"2025 · 4 months"), plus `year` and `durationMonths` for sorting only. Experience keeps real dates —
a job does have a start and an end.

### D-009 · Admin panel is launch scope
**Date:** 2026-09-06 · **Status:** Accepted

Requested: log in on the site itself and edit everything. Adds ~14h and moves launch out by roughly
a week, but a site you can't update without a deploy stops getting updated.

### D-010 · No monorepo tooling
**Date:** 2026-09-06 · **Status:** Accepted

A root Makefile over Turborepo/pnpm workspaces. Two apps in different languages share no JS
dependencies, so a JS monorepo tool would add config for no benefit.

---

## Template for new decisions

```markdown
### D-0NN · Title
**Date:** YYYY-MM-DD · **Status:** Proposed | Accepted | Superseded by D-0NN

What we decided, and the reasoning.

*Rejected:* the alternatives, and why not.
*Cost accepted:* what we're knowingly giving up.
```

Anything architectural that took more than ten minutes to think about goes here. Six months from now
the reasoning is worth more than the conclusion.
