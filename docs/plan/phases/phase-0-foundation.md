# Phase 0 · Foundation & Infrastructure

**~6 hours** · Status: 🟡 Local scaffold done. Cloud steps deferred with billing — they are not
needed until Phase 6, so this does not block Phases 1–5.

> **Goal:** A working local development environment and a fully provisioned Firebase/GCP
> project, with infrastructure defined as code from the very first commit.

---

## Prerequisites

- [ ] [Decisions](../decisions.md) answered — especially the project id and Blaze
- [ ] Repo pushed to GitHub
- [x] A Google account for the Firebase project *(personal, not the work account)*

**Tools** — all already installed and verified:

| Tool | Required | You have |
|---|---|---|
| Node | 22+ | 22.20.0 ✅ |
| Python | 3.13 | 3.13 via Homebrew ✅ *(system 3.9 — use the Homebrew one)* |
| Firebase CLI | 14+ | 14.20.0 ✅ |
| gcloud | latest | 543.0.0 ✅ |
| Terraform | 1.9+ | 1.16.0 ✅ *(needs the `hashicorp/tap` — it was removed from homebrew-core)* |
| uv | latest | 0.9.3 ✅ |

---

## Tasks

### 0.1 · Manual bootstrap — ~20 min, you must do these

These can't be Terraformed. See [04 · Infrastructure](../04-infrastructure.md#what-terraform-cant-do).

- [x] Create the GCP project `nikunjramani-in`
- [ ] Attach a billing account (**Blaze**)
- [x] Add Firebase to the project
- [ ] Set the budget alert to ₹500 with 50/90/100% notifications
- [ ] Configure the OAuth consent screen (External, your email as support contact)
- [ ] Enable the **Google** sign-in provider in Firebase Auth
- [ ] Create the Terraform state bucket

`infra/scripts/bootstrap.sh` handles everything with a CLI; the console-only steps are printed as a
checklist as it runs.

### 0.2 · Repo scaffold

- [x] Root `Makefile` with all targets ([01 · Repo Architecture](../01-repo-architecture.md#the-makefile))
- [x] `architecture/`, `frontend/`, `backend/`, `infra/`, `docs/` directory trees
- [x] `docs/RUNBOOK.md`, `docs/ADR/` seeded
- [x] `.nvmrc` (22) and `.python-version` (3.13)

### 0.3 · Terraform

- [x] `backend.tf` — GCS remote state with locking
- [x] `modules/project` — enable APIs, labels, budget
- [x] `modules/iam` — least-privilege service accounts
- [x] `modules/firestore` — database, indexes, rules release
- [x] `modules/storage` — buckets, CORS, lifecycle
- [x] `modules/secrets` — Secret Manager entries
- [x] `modules/monitoring` — uptime check, error alert
- [x] `envs/prod/main.tf` wiring them together
- [ ] `terraform init && terraform plan` reviewed, then applied

> `modules/functions` and `modules/app-hosting` are stubbed now, filled in Phases 3 and 6 — there's
> nothing to deploy into them yet.

### 0.4 · Security rules

- [x] `infra/rules/firestore.rules` per [03 · Security](../03-security.md)
- [x] `infra/rules/storage.rules`
- [x] `infra/rules/firestore.indexes.json` (empty to start)
- [ ] Deployed and verified: an anonymous client read succeeds, a write fails

### 0.5 · Admin claim

- [ ] Sign in once to create your Firebase Auth user
- [ ] Run `infra/scripts/set_admin_claim.py <your-uid>`
- [ ] Verify the claim appears in a freshly minted ID token

### 0.6 · Frontend skeleton

- [x] `create-next-app` — TypeScript, App Router, Tailwind v4, ESLint
- [ ] `shadcn/ui` initialised *(deferred to Phase 2, with the design tokens)*
- [x] Firebase Admin SDK + client SDK wired in `lib/firebase/`
- [x] `tsconfig.json` strict, path aliases (`@/…`)
- [x] ESLint boundary rule: `(site)` may not import from `(admin)`
- [x] `npm run dev` renders a placeholder page

### 0.7 · Backend skeleton

- [x] `backend/functions/` with `uv` and `pyproject.toml`, Python 3.13
- [x] `firebase.json` with `"runtime": "python313"`
- [x] `shared/` skeleton — `core/`, `api.py`, `repositories/`
- [x] `shared/api.py` — `make_function()`, the FastAPI + `a2wsgi` wrapper
- [x] **One proof-of-concept domain**: `src/system/` exporting `api_system` with `/health`
- [x] `main.py` importing and re-exporting it
- [x] Rewrite for it in `frontend/next.config.ts`
- [x] `ruff` + `mypy --strict` + `import-linter` configured and clean
- [ ] Firebase emulators (Firestore, Auth, Storage, Functions) start
- [ ] `/health` responds through the emulator **via the rewrite**, not the raw function URL

### 0.8 · Wire it together

- [ ] `make setup` installs both sides from scratch
- [ ] `make dev` runs Next.js + emulators together
- [x] `make lint` and `make test` pass on the empty projects
- [x] `docs/RUNBOOK.md` documents local setup end to end

---

## Definition of done

1. `make dev` starts the Next.js dev server **and** the Firebase emulators with one command
2. `terraform plan` reports no changes
3. An anonymous Firestore read succeeds; an anonymous write is denied
4. Your account holds the `admin: true` claim
5. A fresh `git clone` + `make setup` + `make dev` works on a clean machine

---

## Gotchas

**System Python is 3.9.** `python3` resolves to `/usr/bin/python3`. Use
`/opt/homebrew/bin/python3.13` explicitly when creating the venv, or `uv` will happily build against
3.9 and the deploy will fail confusingly later.

**Terraform state bucket is chicken-and-egg.** It must exist before `terraform init`, so it's
created by `bootstrap.sh` and then never touched by Terraform.

**Firebase resources need `google-beta`.** If a resource 404s with the standard provider, it wants
the beta one. Expected, not a bug.

**Don't enable Firestore in Datastore mode.** It's irreversible and would sink the project. Native
mode, always.

**Budget alerts notify — they don't cap.** They're a smoke alarm, not a sprinkler. `max_instances`
is what actually bounds spend.

---

**Next:** [Phase 1 · Schemas & Codegen](./phase-1-schemas.md)
