# Phase 0 · Foundation & Infrastructure

**~6 hours** · Status: ⬜ Not started

> **Goal:** A working local development environment and a fully provisioned Firebase/GCP
> project, with infrastructure defined as code from the very first commit.

---

## Prerequisites

- [ ] [Decisions](../decisions.md) answered — especially the project id and Blaze
- [ ] Repo pushed to GitHub
- [ ] A Google account for the Firebase project *(personal, not the work account)*

**Tools** — all already installed and verified:

| Tool | Required | You have |
|---|---|---|
| Node | 22+ | 22.20.0 ✅ |
| Python | 3.13 | 3.13 via Homebrew ✅ *(system 3.9 — use the Homebrew one)* |
| Firebase CLI | 14+ | 14.20.0 ✅ |
| gcloud | latest | 543.0.0 ✅ |
| Terraform | 1.9+ | ⬜ `brew install terraform` |
| uv | latest | ⬜ `brew install uv` |

---

## Tasks

### 0.1 · Manual bootstrap — ~20 min, you must do these

These can't be Terraformed. See [04 · Infrastructure](../04-infrastructure.md#what-terraform-cant-do).

- [ ] Create the GCP project `nikunjramani-in`
- [ ] Attach a billing account (**Blaze**)
- [ ] Add Firebase to the project
- [ ] Set the budget alert to ₹500 with 50/90/100% notifications
- [ ] Configure the OAuth consent screen (External, your email as support contact)
- [ ] Enable the **Google** sign-in provider in Firebase Auth
- [ ] Create the Terraform state bucket

`infra/scripts/bootstrap.sh` handles everything with a CLI; the console-only steps are printed as a
checklist as it runs.

### 0.2 · Repo scaffold

- [ ] Root `Makefile` with all targets ([01 · Repo Architecture](../01-repo-architecture.md#the-makefile))
- [ ] `architecture/`, `frontend/`, `backend/`, `infra/`, `docs/` directory trees
- [ ] `docs/RUNBOOK.md`, `docs/ADR/` seeded
- [ ] `.nvmrc` (22) and `.python-version` (3.13)

### 0.3 · Terraform

- [ ] `backend.tf` — GCS remote state with locking
- [ ] `modules/project` — enable APIs, labels, budget
- [ ] `modules/iam` — least-privilege service accounts
- [ ] `modules/firestore` — database, indexes, rules release
- [ ] `modules/storage` — buckets, CORS, lifecycle
- [ ] `modules/secrets` — Secret Manager entries
- [ ] `modules/monitoring` — uptime check, error alert
- [ ] `envs/prod/main.tf` wiring them together
- [ ] `terraform init && terraform plan` reviewed, then applied

> `modules/functions` and `modules/app-hosting` are stubbed now, filled in Phases 3 and 6 — there's
> nothing to deploy into them yet.

### 0.4 · Security rules

- [ ] `infra/rules/firestore.rules` per [03 · Security](../03-security.md)
- [ ] `infra/rules/storage.rules`
- [ ] `infra/rules/firestore.indexes.json` (empty to start)
- [ ] Deployed and verified: an anonymous client read succeeds, a write fails

### 0.5 · Admin claim

- [ ] Sign in once to create your Firebase Auth user
- [ ] Run `infra/scripts/set_admin_claim.py <your-uid>`
- [ ] Verify the claim appears in a freshly minted ID token

### 0.6 · Frontend skeleton

- [ ] `create-next-app` — TypeScript, App Router, Tailwind v4, ESLint
- [ ] `shadcn/ui` initialised
- [ ] Firebase Admin SDK + client SDK wired in `lib/firebase/`
- [ ] `tsconfig.json` strict, path aliases (`@/…`)
- [ ] ESLint boundary rule: `(site)` may not import from `(admin)`
- [ ] `npm run dev` renders a placeholder page

### 0.7 · Backend skeleton

- [ ] `backend/functions/` with `uv` and `pyproject.toml`, Python 3.13
- [ ] `firebase.json` with `"runtime": "python313"`
- [ ] FastAPI app factory + `a2wsgi` wrapper + `/health`
- [ ] `ruff` + `mypy --strict` configured and clean
- [ ] Firebase emulators (Firestore, Auth, Storage, Functions) start
- [ ] `/health` responds through the emulator

### 0.8 · Wire it together

- [ ] `make setup` installs both sides from scratch
- [ ] `make dev` runs Next.js + emulators together
- [ ] `make lint` and `make test` pass on the empty projects
- [ ] `docs/RUNBOOK.md` documents local setup end to end

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
