# Frontend decisions

Next.js 16 App Router on Firebase App Hosting. Root: [frontend/](../../frontend/).
Flow: [CODE_FLOW §3–7](../CODE_FLOW.md#3--a-visitor-reads-a-page). Entries FE-01…FE-20 were
backfilled on 2026-10-16 from the code and its history.

## Reading content

### ~~FE-01~~ Superseded by [FE-26](#fe-26--pages-read-through-the-python-apis-public-routes) · Pages read Firestore directly with the Admin SDK

- **Where:** [src/lib/data/](../../frontend/src/lib/data/), [src/lib/firebase/admin.ts](../../frontend/src/lib/firebase/admin.ts)
- **Decision:** Server Components call `lib/data/*`, which query Firestore with the Admin SDK under
  App Hosting's ambient, read-only identity. No page data goes through Python.
- **Why:** a function cold start would sit on every page view; reads need no business rules.
- **Related:** ADR 0005

### FE-02 · `import "server-only"` on every Admin-SDK file

- **Where:** `lib/firebase/admin.ts`, `admin/auth/server.ts`, the `api/admin/session` route handler
  (since FE-26 the Admin SDK is used for Firebase Auth only; `lib/data/*` keeps the guard because
  it holds the server-side API calls)
- **Why:** without it, an accidental import from a Client Component ships credentials to the browser
  and nothing fails; with it, that mistake is a build error.

### ~~FE-03~~ Superseded by [FE-26](#fe-26--pages-read-through-the-python-apis-public-routes) · Confidential client details are stripped in `lib/data`, never in a component

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

- **Where:** `reachable_by_url` in [ProjectService](../../backend/functions/src/content/projects/service.py) and `CrudService.list_public` (moved from `lib/data` by FE-26)
- **Why:** guessing a draft's slug must not preview it; an unlisted project is shareable by link
  without appearing in lists or the sitemap.

### ~~FE-06~~ Superseded by [FE-26](#fe-26--pages-read-through-the-python-apis-public-routes) · Timestamps convert in one place; the id rides beside the data

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

- **Where:** [src/proxy.ts](../../frontend/src/proxy.ts); [(protected)/layout.tsx](../../frontend/src/app/%28admin%29/admin/%28protected%29/layout.tsx); [admin/auth/server.ts](../../frontend/src/admin/auth/server.ts)
- **Decision:** the proxy only checks a `session` cookie exists; the protected layout verifies it
  (`verifySessionCookie(..., checkRevoked=true)`) and the `admin` claim.
- **Why:** logged-out visitors bounce without crypto; Next's own guidance is not to rely on the
  proxy alone. Neither is security — the API re-verifies every write (BE-16).

### FE-09 · A session cookie for navigation; a fresh ID token for every API call

- **Where:** [app/(admin)/api/admin/session/route.ts](../../frontend/src/app/%28admin%29/api/admin/session/route.ts); [admin/api-client/client.ts](../../frontend/src/admin/api-client/client.ts)
- **Decision:** after Google sign-in the ID token is exchanged for a 5-day httpOnly cookie; API calls
  attach `getIdToken()` after `authStateReady()`.
- **Why:** ID tokens last an hour and are awkward across page loads — cookies suit navigation. The
  first fetch after a full load ran before the SDK restored its session and failed "not signed in";
  `authStateReady()` waits for that.

### FE-10 · A 401 from the API is a hard navigation to login

- **Where:** `rawFetch` in admin/api-client/client.ts
- **Why:** helpers have no router; a full reload also clears whatever stale state caused the 401.

### FE-11 · Admin saves send a real merge patch

- **Where:** [admin/lib/merge-patch.ts](../../frontend/src/admin/lib/merge-patch.ts) — `toMergePatch(original, edited)`
- **Why:** a cleared field is `undefined`, which `JSON.stringify` drops — sending form values could
  never clear anything. The diff turns clears into `null` (BE-10).

### FE-12 · A signed-in non-admin sees a refusal, not a redirect

- **Where:** `sign-in-panel.tsx` (clears the session and signs out), `(protected)/layout.tsx`
- **Why:** redirecting a valid non-admin to login loops forever — they *can* sign in, they just aren't authorised.

## Admin forms

### FE-13 · Forms render from generated schemas

- **Where:** [admin/components/schema-form/](../../frontend/src/admin/components/schema-form/), `src/generated/admin-schemas.ts`
- **Decision:** `<SchemaForm>` walks the generated schema and Zod validator to choose controls.
- **Why:** a new schema field should appear in the admin with no form code (ADR 0006, 0009).

### FE-14 · Unsaved form drafts autosave to `localStorage`, failing silently

- **Where:** `schema-form.tsx` (`admin-draft:` keys)
- **Why:** losing a long edit to a reload hurts; private mode and quota errors must not break the form
  over a convenience.

### FE-15 · The CSV export downloads through `fetch` + a Blob URL

- **Where:** `apiFetchBlob` in admin/api-client/client.ts
- **Why:** a plain `<a href>` can't carry the `Authorization` header the API requires.

## Public site

### FE-16 · App Check's SDK loads only with the contact form, and starts early

- **Where:** [site/lib/app-check.ts](../../frontend/src/site/lib/app-check.ts)
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

### ~~FE-19~~ Superseded by [FE-22](#fe-22--each-surface-is-a-folder-imports-point-one-way) · Public code can't import admin code — ESLint enforces it

- **Where:** `no-restricted-imports` in [eslint.config.mjs](../../frontend/eslint.config.mjs)
- **Why:** one import would ship the admin editor, the form renderer and the client SDK to every visitor.
- **Outcome:** one-way only today — admin code may import site components (the project preview does).

### FE-20 · Fonts are self-hosted at build time; dark theme by default

- **Where:** [site/fonts.ts](../../frontend/src/site/fonts.ts) and [admin/fonts.ts](../../frontend/src/admin/fonts.ts) (`next/font/google`); each root layout (`next-themes` with `defaultTheme="dark"`)
- **Why:** `next/font` downloads at build — no runtime request to Google, no flash of unstyled text.

## Surfaces

### FE-21 · Two root layouts, one stylesheet each, scoped with `@source`

- **Where:** [app/(site)/layout.tsx](../../frontend/src/app/%28site%29/layout.tsx), [app/(admin)/layout.tsx](../../frontend/src/app/%28admin%29/layout.tsx), [site/site.css](../../frontend/src/site/site.css), [admin/admin.css](../../frontend/src/admin/admin.css), [app/global-not-found.tsx](../../frontend/src/app/global-not-found.tsx)
- **Decision:** each route group renders its own `<html>` and imports its own stylesheet; each
  stylesheet imports Tailwind with `source(none)` and lists the folders it may use. Both import
  `shared/styles/base.css` for the common tokens. Unmatched URLs get `global-not-found.tsx`
  (`experimental.globalNotFound`), styled as the site without nav or footer.
- **Why:** the site is being redesigned while the admin stays as is; one stylesheet meant every
  token change hit both, and every admin utility shipped to visitors. Without a top-level layout
  there's nowhere for a normal 404 to render, hence the global one.
- **Outcome:** site CSS ≈21 KB with no admin classes; admin CSS ≈27 KB. Costs: a full page load
  crossing `/admin` ↔ site; `<html>` + theme provider written three times; a new component folder
  must be added to its surface's `@source` or its classes silently don't generate.
- **Related:** ADR 0021 · FE-22
- **Since:** 2026-10-16

### FE-22 · Each surface is a folder; imports point one way

- **Where:** `src/site/`, `src/admin/`, `src/shared/`, `src/lib/`; rules in [eslint.config.mjs](../../frontend/eslint.config.mjs)
- **Decision:** public-only code lives in `site/`, admin-only code (API client, session cookie
  code, merge patch, formatting) in `admin/`, UI used by both in `shared/`, non-UI used by both in
  `lib/`. ESLint forbids `site` → `admin`, and `shared`/`lib` → either surface. `admin` →
  `site/components` stays allowed.
- **Why:** FE-19 stopped the worst import, but `lib/` still mixed admin-only helpers with shared
  ones, so the path didn't say who owned a file. The admin's project editor previews with the
  real `ProjectDetailView` and `Markdown` so the preview can't drift from the page — that one
  crossing is deliberate.
- **Outcome:** ownership is visible from the path and enforced by lint. Cost: the admin preview
  renders site components with admin tokens, so after the redesign it matches the page in
  structure, not in colour and type.
- **Related:** ADR 0021 · supersedes FE-19
- **Since:** 2026-10-16

### FE-23 · The site has its own typefaces and tokens; the admin keeps Geist

- **Where:** [site/fonts.ts](../../frontend/src/site/fonts.ts) (Archivo with its width axis, IBM Plex Mono 400/500), [site/site.css](../../frontend/src/site/site.css) tokens; [admin/fonts.ts](../../frontend/src/admin/fonts.ts)
- **Decision:** fonts are per surface, not shared. The site's tokens override `base.css` in
  `site.css` only. Archivo is loaded with `axes: ["wdth"]` so headings can stretch
  (`font-stretch-112%`/`125%`) without a second display family.
- **Why:** the Technical redesign (.docs/DESIGN.md) changes type and colour for visitors only;
  putting the faces in `shared/` would have made the admin download them too.
- **Outcome:** each surface's CSS declares only its own families. Cost: the width axis makes the
  Archivo file larger than a weight-only cut. Hex tokens in `site.css` are deliberate (the palette
  was specified in hex and contrast-checked as such); components still use token names only.
- **Related:** ADR 0021 · FE-20 · FE-21
- **Since:** 2026-10-16

### FE-24 · Site structure comes from `SpecTable` and `SpecSection`, not cards

- **Where:** [site/components/spec.tsx](../../frontend/src/site/components/spec.tsx), [site/components/styles.ts](../../frontend/src/site/components/styles.ts)
- **Decision:** every section is a `SpecSection` (label column + content) and every set of facts
  is a `SpecTable` (ruled key/value rows that drop empty values). Button and chip classes are
  string constants, not components.
- **Why:** the design is a spec sheet (DESIGN.md); two components make that structure the easy
  path on every page. `SpecTable` dropping falsy rows means a page can pass
  `profile?.location && {…}` and never render an empty key (ADR 0008). Constants rather than
  `<Button>` because links, anchors and submit buttons all need the same look and a component
  would have to polymorph over all three.
- **Outcome:** pages read as data → layout with no per-page spacing decisions. It also surfaced
  `role`, `team` and `metrics` on projects, which the old detail view never rendered. Cost: the
  admin preview uses these with admin tokens, so it doesn't match the page's colours (FE-22).
- **Related:** ADR 0008 · .docs/DESIGN.md
- **Since:** 2026-10-16

### FE-25 · Admin route handlers live in `(admin)`; "API" means one thing per folder

- **Where:** [app/(admin)/api/admin/](../../frontend/src/app/%28admin%29/api/admin/), [admin/api-client/](../../frontend/src/admin/api-client/), [admin/auth/](../../frontend/src/admin/auth/) (the media-usage route and `admin/data/` were removed by FE-26)
- **Decision:** the two Next.js route handlers moved from `app/api/admin/` into the `(admin)` route
  group (URLs unchanged: `/api/admin/session`, `/api/admin/media/[id]/usage`). The browser-side
  Python API client is `admin/api-client/`, not `admin/api/`. Auth is one folder: `cookie.ts`
  (name and lifetime, no imports — safe for `proxy.ts`), `server.ts` (verify), `client.ts`
  (sign-in exchange). The admin-only media-usage read moved from `lib/data/` to `admin/data/`.
- **Why:** route handlers must sit under `app/` to be served, but at `app/api/` they belonged to
  neither surface; and two folders both named `api` — one Next server endpoints, one a client for
  Python — read as the same thing. The cookie name was a string literal in three files.
- **Outcome:** every file's owner is visible from its path, and `lib/` holds only what both
  surfaces use. Cost: the URLs keep `/api/admin/…` rather than moving under `/admin`, because the
  proxy's matcher redirects cookieless `/admin/*` requests — the sign-in exchange has no cookie yet.
- **Related:** ADR 0021 · FE-08 · FE-09 · FE-22
- **Since:** 2026-10-16


### FE-26 · Pages read through the Python API's `/public` routes

- **Where:** [lib/data/api.ts](../../frontend/src/lib/data/api.ts) (`listPublic`, `getPublic`, `WithId`), [lib/data/](../../frontend/src/lib/data/)
- **Decision:** Server Components still call `lib/data/*` with the same function names, but each
  one now calls a content function's unauthenticated `GET /public` route, server-to-server and
  straight to the function URL, `cache: "no-store"`. The frontend has no Firestore SDK: ESLint
  forbids importing one, and the App Hosting identity has no Firestore role. Visibility,
  confidential-client stripping and timestamp conversion all happen in the API (BE-40). The media
  usage check moved to the API too (BE-39), so `app/(admin)/api/admin/media/` and `admin/data/`
  are gone; the session route is the only Next.js route handler left.
- **Why:** the owner wants one place that knows the database, so changing it touches only the
  backend; and rules that protect data must hold for every caller, not just the UI.
- **Outcome:** pages and components didn't change — only what `lib/data` does underneath. Cost: a
  page view after an idle period waits for the content functions' cold start.
- **Related:** ADR 0022 · supersedes FE-01, FE-03, FE-06 · BE-39 · BE-40
- **Since:** 2026-10-20

### FE-27 · The API's URL scheme is written once, in `lib/backend.ts`

- **Where:** [lib/backend.ts](../../frontend/src/lib/backend.ts) — `API_PREFIX`, `functionName`, `functionUrl`
- **Decision:** the `/api/v1` prefix, the `api_<domain>_<sub>` naming and the functions base URL
  live in one module, used by `next.config.ts` (rewrites), `admin/api-client/client.ts`,
  `site/lib/contact.ts` and `lib/data/api.ts`. Route names still come from
  `architecture/api-routes.json`.
- **Why:** the prefix and the function-name rule were each repeated in three files, so changing
  the URL scheme meant hunting for every copy.
- **Outcome:** a URL-scheme change is one edit. No imports, so `next.config.ts` can load it.
- **Related:** FE-07
- **Since:** 2026-10-20
