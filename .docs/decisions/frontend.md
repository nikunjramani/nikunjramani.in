# Frontend decisions

Next.js 16 App Router on Firebase App Hosting. Root: [frontend/](../../frontend/).
Flow: [CODE_FLOW §3–7](../CODE_FLOW.md#3--a-visitor-reads-a-page). Entries FE-01…FE-20 were
backfilled on 2026-10-16 from the code and its history.

## Reading content

### FE-01 · Pages read Firestore directly with the Admin SDK

- **Where:** [src/lib/data/](../../frontend/src/lib/data/), [src/lib/firebase/admin.ts](../../frontend/src/lib/firebase/admin.ts)
- **Decision:** Server Components call `lib/data/*`, which query Firestore with the Admin SDK under
  App Hosting's ambient, read-only identity. No page data goes through Python.
- **Why:** a function cold start would sit on every page view; reads need no business rules.
- **Related:** ADR 0005

### FE-02 · `import "server-only"` on every Admin-SDK file

- **Where:** `lib/firebase/admin.ts`, `lib/data/*`, `lib/auth/session.ts`, the `api/admin/*` route handlers
- **Why:** without it, an accidental import from a Client Component ships credentials to the browser
  and nothing fails; with it, that mistake is a build error.

### FE-03 · Confidential client details are stripped in `lib/data`, never in a component

- **Where:** `stripConfidentialClient` in [lib/data/projects.ts](../../frontend/src/lib/data/projects.ts)
- **Why:** React serialises props into the RSC payload whether or not a component renders them; the
  data layer is the only place that can guarantee the name and logo never reach the browser.

### FE-04 · Render per request; dedupe within a request only

- **Where:** `revalidate = 0` in `(site)/layout.tsx` and `sitemap.ts`; `React.cache` around readers
- **Decision:** no persistent content cache, no `unstable_cache`, no `"use cache"`.
- **Why:** a cached page survived edits on other instances and behind the CDN (stale content after
  publish); the revalidation webhook added to fix it was more moving parts than the problem.
- **Outcome:** every edit is visible on the next request. Cost: one Firestore read set per view —
  negligible at this traffic.
- **Related:** ADR 0014, ADR 0015

### FE-05 · Drafts 404 by URL; `unlisted` is reachable but never listed

- **Where:** `getProjectBySlug` (`REACHABLE_BY_URL`), `getAllProjects`
- **Why:** guessing a draft's slug must not preview it; an unlisted project is shareable by link
  without appearing in lists or the sitemap.

### FE-06 · Timestamps convert in one place; the id rides beside the data

- **Where:** [lib/data/convert.ts](../../frontend/src/lib/data/convert.ts) — `fromSnapshot`, `WithId<T>`
- **Why:** mirrors the backend (BE-12, BE-13): generated types expect ISO strings and have no `id`.

## Calling the API

### FE-07 · Same-origin `/api/v1/*`, rewritten by Next.js to each function

- **Where:** `rewrites()` in [next.config.ts](../../frontend/next.config.ts), generated `api-routes.ts`
- **Decision:** `/api/v1/<domain>/<sub>/*` → `$FUNCTIONS_BASE_URL/api_<domain>_<sub>/*`.
- **Why:** App Hosting has no rewrites of its own (unlike classic Hosting). One origin also means no
  CORS preflight. `FUNCTIONS_BASE_URL` must be available at **build** time — Next serialises rewrites.
- **Outcome:** cost: one extra hop through the already-warm Next server.
- **Related:** ADR 0011, ADR 0017, SC-04

### FE-08 · Two admin gates: a cheap presence check, then real verification

- **Where:** [src/proxy.ts](../../frontend/src/proxy.ts); [(protected)/layout.tsx](../../frontend/src/app/%28admin%29/admin/%28protected%29/layout.tsx); [lib/auth/session.ts](../../frontend/src/lib/auth/session.ts)
- **Decision:** the proxy only checks a `session` cookie exists; the protected layout verifies it
  (`verifySessionCookie(..., checkRevoked=true)`) and the `admin` claim.
- **Why:** logged-out visitors bounce without crypto; Next's own guidance is not to rely on the
  proxy alone. Neither is security — the API re-verifies every write (BE-16).

### FE-09 · A session cookie for navigation; a fresh ID token for every API call

- **Where:** [app/api/admin/session/route.ts](../../frontend/src/app/api/admin/session/route.ts); [lib/api/client.ts](../../frontend/src/lib/api/client.ts)
- **Decision:** after Google sign-in the ID token is exchanged for a 5-day httpOnly cookie; API calls
  attach `getIdToken()` after `authStateReady()`.
- **Why:** ID tokens last an hour and are awkward across page loads — cookies suit navigation. The
  first fetch after a full load ran before the SDK restored its session and failed "not signed in";
  `authStateReady()` waits for that.

### FE-10 · A 401 from the API is a hard navigation to login

- **Where:** `rawFetch` in lib/api/client.ts
- **Why:** helpers have no router; a full reload also clears whatever stale state caused the 401.

### FE-11 · Admin saves send a real merge patch

- **Where:** [lib/merge-patch.ts](../../frontend/src/lib/merge-patch.ts) — `toMergePatch(original, edited)`
- **Why:** a cleared field is `undefined`, which `JSON.stringify` drops — sending form values could
  never clear anything. The diff turns clears into `null` (BE-10).

### FE-12 · A signed-in non-admin sees a refusal, not a redirect

- **Where:** `sign-in-panel.tsx` (clears the session and signs out), `(protected)/layout.tsx`
- **Why:** redirecting a valid non-admin to login loops forever — they *can* sign in, they just aren't authorised.

## Admin forms

### FE-13 · Forms render from generated schemas

- **Where:** [components/admin/schema-form/](../../frontend/src/components/admin/schema-form/), `src/generated/admin-schemas.ts`
- **Decision:** `<SchemaForm>` walks the generated schema and Zod validator to choose controls.
- **Why:** a new schema field should appear in the admin with no form code (ADR 0006, 0009).

### FE-14 · Unsaved form drafts autosave to `localStorage`, failing silently

- **Where:** `schema-form.tsx` (`admin-draft:` keys)
- **Why:** losing a long edit to a reload hurts; private mode and quota errors must not break the form
  over a convenience.

### FE-15 · The CSV export downloads through `fetch` + a Blob URL

- **Where:** `apiFetchBlob` in lib/api/client.ts
- **Why:** a plain `<a href>` can't carry the `Authorization` header the API requires.

## Public site

### FE-16 · App Check's SDK loads only with the contact form, and starts early

- **Where:** [lib/firebase/app-check.ts](../../frontend/src/lib/firebase/app-check.ts)
- **Decision:** dynamic `import("firebase/app-check")` on first use; `initAppCheck()` runs when the
  form mounts so reCAPTCHA has signals by submit time. No site key (local dev) → off.
- **Related:** ADR 0020, BE-19

### FE-17 · No Firestore client SDK in the browser at all

- **Where:** [lib/firebase/client.ts](../../frontend/src/lib/firebase/client.ts) exposes Auth only
- **Why:** reads are server-side (FE-01) and writes go through the API (ADR 0007); a client SDK would
  only be an attack surface and bundle weight.

### FE-18 · Security headers live in `next.config.ts`; staging adds `noindex`

- **Where:** `headers()` in next.config.ts; `SITE_INDEXABLE` in `apphosting.staging.yaml`
- **Why:** App Hosting serves Next's headers as-is; a preview must never be indexed. CSP is not set yet.

### FE-19 · Public code can't import admin code — ESLint enforces it

- **Where:** `no-restricted-imports` in [eslint.config.mjs](../../frontend/eslint.config.mjs)
- **Why:** one import would ship the admin editor, the form renderer and the client SDK to every visitor.
- **Outcome:** one-way only today — admin code may import site components (the project preview does).

### FE-20 · Fonts are self-hosted at build time; dark theme by default

- **Where:** `src/app/layout.tsx` (`next/font/google` Geist, `next-themes` with `defaultTheme="dark"`)
- **Why:** `next/font` downloads at build — no runtime request to Google, no flash of unstyled text.
