---
paths:
  - "frontend/**"
---

# Frontend rules (Next.js 16 on App Hosting)

The `add-page` skill has the step-by-step; decisions behind the code are in
`.docs/decisions/frontend.md`. **Read `frontend/node_modules/next/dist/docs/` before writing
Next code** — Next 16 differs from what you remember (`proxy.ts`, not `middleware.ts`;
async `params`/`searchParams`/`cookies()`).

## Load-bearing

- **The frontend never touches Firestore** (ADR 0022). Server Components read through
  `lib/data/*`, which calls the Python API's public `GET /public` routes (`lib/data/api.ts`).
  Admin reads and writes go through `admin/api-client/*`. ESLint forbids importing any Firestore
  SDK; the App Hosting identity has no Firestore role. A new page needing new data needs a new
  `/public` route in the backend first.
- **`import "server-only"`** at the top of every file touching the Admin SDK (Auth only, for the
  session cookie) or calling the API from the server (`lib/data/*`) — without it the failure
  mode is a leaked credential, not a build error.
- **`"use client"` as deep as possible** — a client `<ThemeToggle>` inside a server `<Nav>`.
- **Confidential data is stripped by the API** (`ProjectService.to_public`), never in a component
  (the RSC payload would still carry it).
- **Fresh reads**: the site renders per request (`revalidate = 0`, ADR 0014). No
  `unstable_cache` / `"use cache"` for content — nothing invalidates it (ADR 0015).
  `React.cache` for per-request dedupe is fine.
- **Generated code is never hand-edited**: `src/generated/` comes from `architecture/` via
  `make gen`.

## Conventions

- Optional fields render conditionally — no empty headings, no placeholders (ADR 0008).
- Public reads return `visibility == "public"` sorted by `order` (the API's `list_public`);
  `unlisted` is reachable by URL (with `noindex`) but never listed or in the sitemap; drafts 404.
- Admin saves send a real merge patch built with `admin/lib/merge-patch.ts`'s `toMergePatch`.
- Admin forms render from the generated schemas (`<SchemaForm>`); a new schema field should need
  no form code.
- Public site code never imports admin code — `eslint.config.mjs` (`no-restricted-imports`)
  fails the build, because it would ship the admin bundle to visitors.

## Where code goes (ADR 0021)

The site and the admin are separate surfaces — separate root layouts, stylesheets and designs.

| Used by | Goes in |
|---|---|
| the public site only | `src/site/` (`components/`, `lib/`), styles in `site/site.css`, fonts in `site/fonts.ts` |
| the admin only | `src/admin/` (`components/`, `api-client/`, `auth/`, `lib/`), styles in `admin/admin.css`, fonts in `admin/fonts.ts` |
| a URL (page, route handler) | `src/app/` — Next only serves what's there. Under `(site)/` or `(admin)/` by owner; keep files thin and import the logic from the surface folder |
| both, UI | `src/shared/` (components, `styles/base.css`) |
| both, non-UI | `src/lib/` (`data/` page reads via the API, `backend.ts` the API's URL scheme, `firebase/` Auth, `utils`, `site`) |

- Imports point one way: `site`/`admin` → `shared`/`lib`/`generated`; `shared` and `lib` never
  import a surface; the admin may import `site/components` (the editor previews with them). ESLint
  enforces all of it.
- Each stylesheet scans only its own folders (`@source`). A new folder holding classes for a
  surface must be added to that surface's `@source` list, or its classes silently won't exist.
- A token change for one surface goes in that surface's stylesheet; `shared/styles/base.css` is
  for what both genuinely share.
- Crossing between `/admin` and the site is a full page load — use `<a>`, not `<Link>`.
- **Two different "APIs":** `app/(admin)/api/` holds the one Next.js *route handler* (served by
  the Next server itself — the session cookie, which only this server can set).
  `admin/api-client/` is the browser-side client for the *Python* API. Never add a Next route
  handler that reads or writes data; that's the Python API's job (ADR 0022).
- `(site)` and `(admin)` are route groups — the parentheses keep the folder name out of the URL.
  That's why the admin is `(admin)/admin/…`: the group owns the layout, the inner `admin`
  folder is the `/admin` URL segment.
- `next/image` with correct `sizes`; design tokens only, no hard-coded hex.
- API calls go to `${API_PREFIX}/<domain>/<sub>/…` (same origin); `next.config.ts` rewrites them to
  the function. Route names come from the generated `api-routes.ts`; the prefix, function naming
  and base URL from `lib/backend.ts` — never write `/api/v1` or a function URL by hand.

## Design work

**The public site's design system is `.docs/DESIGN.md` — read it before touching site UI.** In
short: build pages from `SpecSection` / `SpecTable` (`site/components/spec.tsx`) and the class
constants in `site/components/styles.ts`; tokens only; Archivo for text (headings stretched), Plex
Mono for data only; the accent means current/primary/measured, never decoration; sentence case, no `·`
separators, no cards for lists; the hero's draw-in is the site's only animation.

For visual design or redesign, use the `frontend-design` skill and check the result with
`web-design-guidelines`; performance review with `react-best-practices`. Accessibility is not
optional: landmarks, keyboard, visible focus, alt text, AA contrast in both themes,
`prefers-reduced-motion`. Verify with `view-source` that real content is server-rendered.
**Localhost Lighthouse scores lie** — only production numbers count (staging's are report-only).
