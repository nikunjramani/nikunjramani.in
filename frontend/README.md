# frontend

Next.js 16 (App Router) — the public site and the `/admin` panel.

- `src/app/(site)/` — public pages, Server Components, server-rendered for SEO
- `src/app/(admin)/` — the authenticated editor, client-rendered
- `src/lib/data/` — the only place Firestore is queried (server-side, Admin SDK)
- `src/lib/api/` — typed client for the Python API (writes only)
- `src/generated/` — codegen output from `architecture/schemas`. Never hand-edit.

Run from the repo root: `make dev` · `make lint` · `make build`

See [CLAUDE.md](../CLAUDE.md) for the rules that apply here, and
[AGENTS.md](./AGENTS.md) for Next.js 16 specifics.
