# CLAUDE.md

Context for working on this repository.

## What this is

The personal website at **nikunjramani.in** — portfolio, projects, writing. A server-rendered
Next.js site whose content lives in Firestore, edited through an admin panel on the site itself,
with a Python API owning every write.

**This repository is public.** Never commit secrets, credentials, personal contact details,
employer names, client names, or anything from a private engagement. Reach for a placeholder and
say so.

**Status:** Phase 0 scaffold done, Phase 1 in progress. Billing is deferred, so development runs
entirely against the **Firebase emulators** — that works for everything up to Phase 6.
Full plan: [`docs/plan/`](./docs/plan/README.md) · Decisions: [`docs/adr/`](./docs/adr/README.md)

## Stack

| | |
|---|---|
| Frontend | Next.js 16 App Router · TypeScript strict · Tailwind v4 · shadcn/ui |
| Backend | Python 3.13 · FastAPI on Cloud Functions for Firebase (2nd gen) |
| Data | Cloud Firestore · Firebase Storage · Firebase Auth |
| Hosting | Firebase App Hosting |
| Infra | Terraform (`google` + `google-beta`) |

## Layout

```
architecture/   JSON Schemas — the single source of truth for every model
frontend/       Next.js app: (site) public + (admin) private
backend/        Python Firebase Functions — shared/ + one domain per function
infra/          Terraform modules + Firestore/Storage rules
docs/plan/      The build plan, per phase
docs/adr/       Architecture decision records
```

## Commands

```bash
make setup   # install both sides
make dev     # Next.js dev server + Firebase emulators
make gen     # regenerate models from architecture/schemas  ← after ANY schema edit
make validate # validate schemas + example fixtures
make lint    # eslint + ruff + mypy --strict + import-linter + terraform fmt
make test    # vitest + pytest
make deploy  # terraform apply + firebase deploy
```

CI runs these exact targets. If it passes locally it passes in CI.

---

## The seven rules

These are load-bearing. Each has an ADR behind it — read it before proposing a change.

**1 · Never hand-edit generated code.**
`frontend/src/generated/` and `backend/functions/generated/` come from `architecture/schemas/`.
Edit the schema, run `make gen`. CI fails on drift. → [ADR 0006](./docs/adr/0006-json-schema-source-of-truth.md)

**2 · Reads never touch Python.**
Next.js Server Components read Firestore directly via the Admin SDK. Python handles writes only.
Never propose routing page data through the API — cold starts would sit on the read path.
→ [ADR 0005](./docs/adr/0005-reads-bypass-python.md)

**3 · Clients never write to Firestore.**
Rules deny all client writes, including admin. Every mutation goes through the Python API so
validation, rate limiting and audit logging can't be bypassed.
→ [ADR 0007](./docs/adr/0007-deny-all-client-writes.md)

**4 · The Admin SDK is server-only.**
Every file touching it starts with `import "server-only"`. Without that guard the failure mode is a
leaked credential, not a build error.

**5 · `"use client"` goes as deep in the tree as possible.**
A client `<ThemeToggle>` inside a server `<Nav>`, never a client `<Nav>`. One misplaced directive
pulls the whole subtree into the browser bundle.

**6 · Backend layering is one-way, and domains don't cross.**
`router → service → repository → Firestore`. Routers do HTTP only. Services hold business rules and
don't know what HTTP is. Repositories are the only code importing the Firestore SDK.

One deployed function per domain, each owning its routes, service, repository, triggers and tests
in `backend/functions/src/<domain>/`. `shared/` may never import from `src/`, and no domain may
import another domain's service or repository — use `shared/` or an event.
→ [ADR 0011](./docs/adr/0011-domain-wise-separate-functions.md)

**7 · Architectural changes get an ADR.**
Anything a stranger would ask "why is it like this?" about. Copy `docs/adr/TEMPLATE.md`, add an
index row, commit it with the change. ADRs are immutable — supersede, never edit.

---

## Conventions

**Optional fields render conditionally.** The project model is ~6 required fields and ~30 optional
ones. A section appears only when its data exists — no empty headings, no `null` placeholders, no
"coming soon". This applies to the public page and the admin form alike.
→ [ADR 0008](./docs/adr/0008-projects-drop-start-end-dates.md)

**Confidential data is stripped server-side.** `client.confidential: true` means the name must never
reach the browser. Filter it in `lib/data/`, not in a component — component-level filtering still
ships the value in the RSC payload.

**Every content collection has `visibility` and `order`.** Public queries filter
`visibility == "public"` and sort by `order`.

**Timestamps** are ISO strings in schemas, Firestore `Timestamp` in the database. Conversion happens
in the repository layer, in exactly one place.

**Secrets** live in Secret Manager, injected by Terraform. Never in `.env` files, never in git.
`NEXT_PUBLIC_*` Firebase config is public by design — the security is in the rules, not in hiding it.

## Gotchas

- **System Python is 3.9.** `python3` resolves to `/usr/bin/python3`. Use the Homebrew 3.13
  explicitly, or `uv` silently builds against 3.9 and it fails at deploy time.
- **Firebase resources need the `google-beta` provider.** A 404 on the standard provider usually
  means this, not a bug.
- **Firestore composite queries need composite indexes.** Generated from `x-firestore.indexes` —
  add the index when you add the query.
- **Cold starts scale with top-level imports.** Keep `main.py` thin; import heavy things inside the
  function that needs them.
- **A new domain needs a rewrite in `frontend/next.config.ts`** (not Firebase Hosting — App Hosting
  has no rewrites). Without it the function deploys fine and looks healthy, but the frontend gets a
  404 that reads like a routing bug. It also needs adding to the `importlinter` contract in
  `backend/functions/pyproject.toml`, or its boundaries go unchecked.
- **Never construct `a2wsgi.ASGIMiddleware` directly.** It starts a persistent background thread
  at construction time, and Werkzeug's dev-server reloader (which `functions-framework` uses
  locally) forks — the child inherits a dead copy of that thread, and every request hangs forever.
  Reproduced directly with `os.fork()`. Use `shared/wsgi_bridge.py` (`wsgi_from_asgi`), which drives
  each request with a fresh `asyncio.run()` instead. See ADR 0003's implementation note.
- **Firebase's own tooling needs `backend/functions/requirements.txt` and a stdlib `venv/`**,
  separate from the `uv`-managed `.venv/` used for lint/test — `make setup-backend` generates both.
  Without them, `firebase deploy` and `firebase emulators:start` cannot detect the runtime or load
  any function at all.
- **A `TestClient` call proves the FastAPI app works, not that the Firebase adapter does.** The
  a2wsgi bug above type-checked cleanly and passed every unit test; it only appeared against the
  real emulator. Phase 3's "deploy `make_function()` to the emulator before building further
  domains" step exists for exactly this gap.
- **Localhost Lighthouse scores lie.** Only production numbers count.
- **Debug a function directly via `functions-framework`, never through
  `firebase emulators:start --only functions`.** Breakpoints don't reliably hit through that
  emulator's own per-function subprocess model. VS Code configs for this are committed in
  `.vscode/` — see [docs/RUNBOOK.md](./docs/RUNBOOK.md#debugging-vs-code).

## Working style

- Read the relevant `docs/plan/phases/` doc before starting a phase — each has prerequisites, a
  definition of done, and a gotchas list written in advance.
- Tick the checkboxes as work completes; update the status table in `docs/plan/README.md`.
- Prefer finishing a phase to starting the next one.
- When a plan doc turns out to be wrong, fix the doc in the same commit as the code.
