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

- **Reads never touch Python** (ADR 0005). Server Components read Firestore through `lib/data/*`
  with the Admin SDK. Never route page data through the API.
- **Clients never write Firestore** (ADR 0007). Admin writes go through `lib/api/*` → the Python
  API. There is no Firestore client SDK in the browser at all.
- **`import "server-only"`** at the top of every file touching the Admin SDK — without it the
  failure mode is a leaked credential, not a build error.
- **`"use client"` as deep as possible** — a client `<ThemeToggle>` inside a server `<Nav>`.
- **Confidential data is stripped in `lib/data/`**, never in a component (the RSC payload would
  still carry it).
- **Fresh reads**: the site renders per request (`revalidate = 0`, ADR 0014). No
  `unstable_cache` / `"use cache"` for content — nothing invalidates it (ADR 0015).
  `React.cache` for per-request dedupe is fine.
- **Generated code is never hand-edited**: `src/generated/` comes from `architecture/` via
  `make gen`.

## Conventions

- Optional fields render conditionally — no empty headings, no placeholders (ADR 0008).
- Public queries filter `visibility == "public"` and sort by `order`; `unlisted` is reachable by
  URL (with `noindex`) but never listed or in the sitemap; drafts 404.
- Admin saves send a real merge patch built with `lib/merge-patch.ts`'s `toMergePatch`.
- Admin forms render from the generated schemas (`<SchemaForm>`); a new schema field should need
  no form code.
- Public site code never imports admin code — `eslint.config.mjs` (`no-restricted-imports`)
  fails the build, because it would ship the admin bundle to visitors.
- `next/image` with correct `sizes`; design tokens only, no hard-coded hex.
- API calls go to `/api/v1/<domain>/<sub>/…` (same origin); `next.config.ts` rewrites them to the
  function, from the generated `api-routes.ts`.

## Design work

For visual design or redesign, use the `frontend-design` skill and check the result with
`web-design-guidelines`; performance review with `react-best-practices`. Accessibility is not
optional: landmarks, keyboard, visible focus, alt text, AA contrast in both themes,
`prefers-reduced-motion`. Verify with `view-source` that real content is server-rendered.
**Localhost Lighthouse scores lie** — only production numbers count (staging's are report-only).
