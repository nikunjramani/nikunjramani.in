# frontend

Next.js 16 (App Router) — the public site and the `/admin` panel, as two separate surfaces
with their own root layouts and stylesheets ([ADR 0021](../.docs/adr/0021-site-and-admin-are-separate-surfaces.md)).

- `src/app/(site)/` — public pages, Server Components, server-rendered for SEO
- `src/app/(admin)/` — the authenticated editor, client-rendered
- `src/site/` — public-only components, helpers and `site.css`
- `src/admin/` — admin-only components, the typed Python API client (`api-client/`, writes only), auth, `admin.css`
- `src/shared/` — UI both surfaces use (theme, fonts, base tokens)
- `src/lib/data/` — every page read, server-side, through the Python API's `/public` routes (the frontend never touches Firestore — ADR 0022)
- `src/lib/backend.ts` — the API's URL scheme (prefix, function names, base URL)
- `src/generated/` — codegen output from `architecture/schemas`. Never hand-edit.

Imports point one way — `site`/`admin` → `shared`/`lib`, and `admin` → `site/components` for the
editor's preview; ESLint fails anything else.

Run from the repo root: `make dev` · `make lint` · `make build`

See [CLAUDE.md](../CLAUDE.md) for the rules that apply here, and
[AGENTS.md](./AGENTS.md) for Next.js 16 specifics.
