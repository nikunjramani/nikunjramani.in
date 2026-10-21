# Phase 9 · Backend on Cloud Run

**One PR** · Status: 🟡 Built in one PR; the cutover runs on merge, then the old functions are
deleted ([ADR 0023](../../adr/0023-backend-as-one-cloud-run-service.md))

> **Goal:** the FastAPI backend runs as **one Cloud Run service** built from one image, with the
> domain/subdomain structure unchanged, Firestore unchanged, and no downtime on the way.

The owner asked for the whole move in a single PR (2026-10-21). The plan this replaces split it
into four; the order of operations that made four safe is kept inside the one merge.

---

## The target, in one picture

```
Browser ──▶ App Hosting (Next.js) ── rewrite /api/v1/* ──┐
           Server Components ──── GET …/public ──────────┤
                                                         ▼
                                    Cloud Run service `api` (asia-south1, 1 vCPU, 1 GiB,
                                    concurrency 80, 0–3 instances, runs as functions-runtime@)
                                    ├── /api/v1/<domain>/<sub>/…   public · AdminClaims · App Check
                                    └── /internal/…                Google OIDC token of functions-runtime@ only
                                              ▲            ▲              ▲
             Eventarc: Storage object.finalized │  Eventarc: Firestore    │  Cloud Scheduler
             (media bucket) ────────────────────┘  contact_messages/*  ───┘  nightly-backup, 02:00 IST
                                                   document.created
                                    │
                                    ▼
                    Firestore · Cloud Storage · Firebase Auth · Secret Manager   (unchanged)
```

**Who owns what:** CI creates and updates the service (`make deploy-api`) and its image
repository (`make api-registry`), as `firebase deploy` did with functions — staging's Terraform
applies only from `main`, so this PR's own preview has to be able to create it. Terraform
(`modules/api`) owns the triggers and the scheduler job that point at it.

## The code layout

```
backend/                          (was backend/functions/)
├── apps/api.py                   mounts every router — the one file that knows them all
├── kernel/app.py                 make_app(): errors, CORS, /docs off in prod, no slash redirects
├── kernel/events.py              InternalCaller + Storage/Firestore event readers
├── src/<domain>/<subdomain>/     routes.py · schemas.py · service.py · repository.py (unchanged)
│   └── events.py                 media/processing · inbox/notifications · ops/backup
├── deploy/<project>.yaml            deployed config (was .env.<project>)
├── deploy/cleanup-policy.json    image retention
├── Dockerfile · .dockerignore
└── tests/                        + apps/, kernel/test_app.py, kernel/test_events.py, */test_events.py
```

Deleted: `main.py`, every `src/*/main.py` and `src/*/*/main.py`, `kernel/http.py`,
`kernel/wsgi_bridge.py`, `requirements.txt`, the `firebase-functions` and `a2wsgi` dependencies,
`firebase.json`'s functions block, `modules/functions`, the second `venv/`.

---

## Prerequisites

- [x] Owner approves the plan (2026-10-21, "create single PR for all backend changes")
- [x] Prod Terraform caught up — the PR #19 apply was approved and applied
- [ ] **Owner, once, before this PR's first preview and its merge** — the new resource types need
      roles on the CI identities (lessons-learned 2026-10-16; `infra.md`):
      ```powershell
      foreach ($p in 'nikunjramani-in-staging','nikunjramani-in') {
        gcloud projects add-iam-policy-binding $p --member="serviceAccount:github-deploy@$p.iam.gserviceaccount.com" --role=roles/artifactregistry.admin --condition=None
        foreach ($r in 'roles/eventarc.admin','roles/cloudscheduler.admin') { gcloud projects add-iam-policy-binding $p --member="serviceAccount:github-terraform@$p.iam.gserviceaccount.com" --role=$r --condition=None }
      }
      ```
      The PR also adds them to `deploy_roles` / `terraform_roles`, so Terraform records them.

## Tasks

### The app
- [x] `kernel/app.py` (from `kernel/http.py`'s app half) with `TrailingSlashFallback` (BE-43)
- [x] `kernel/events.py`: `InternalCaller` (BE-42), `storage_object`, `firestore_document`
- [x] `events.py` in media/processing, inbox/notifications, ops/backup (BE-44)
- [x] `apps/api.py`: `ROUTES` + `INTERNAL`, `create_app()` (BE-41)
- [x] `kernel/config.py`: `GOOGLE_CLOUD_PROJECT`, `SERVICE_URL` (comma-separated audiences)
- [x] import-linter: `apps` forbidden to everything else; layers `routes | events`
- [x] Dockerfile (python 3.13.16-slim-trixie, uv 0.13.4 — looked up 2026-10-21), `.dockerignore`
- [x] Dependencies: − `firebase-functions`, − `a2wsgi`, + `uvicorn` 0.54.0, + `google-events` 0.14.0
      (decoding verified locally with a real protobuf round trip)
- [x] Tests: registry rewritten for `apps/api.py`; `tests/apps/test_api.py`, `test_app.py`,
      `test_events.py`, one `test_events.py` per triggered subdomain; Functions-only tests removed
- [x] `backend/functions/` → `backend/`, every path updated

### Infrastructure and CI
- [x] `modules/api`: Eventarc triggers (Storage, Firestore/protobuf) + `nightly-backup` scheduler
- [x] `modules/iam`: deploy and terraform roles as above; compute-default trigger bindings removed
- [x] `modules/functions` and `functions_deployed` removed; `api_url` output
- [x] Makefile `api-registry`, `deploy-api`, `dev-backend`; `make dev` runs the API
- [x] `.github/actions/cloud-run-deploy`; `api` target in `pr.yml` / `deploy.yml`, deployed before
      `firebase-deploy`; `firebase-deploy` no longer deploys functions
- [x] `firebase.json` without functions; `.vscode` debug config runs uvicorn

### Frontend
- [x] `lib/backend.ts` → `apiUrl`; one rewrite in `next.config.ts`; `API_BASE_URL` in
      `apphosting*.yaml` (deterministic service URLs); `BACKEND_ROUTES` dropped from codegen

### Verify — in the PR
- [ ] CI green: backend (ruff, mypy, import-linter, full pytest on the emulator), frontend,
      schemas, both Terraform plans
- [ ] Staging preview: the image builds, `api` deploys, smoke test passes; every site page and the
      admin work through it; `/internal/jobs/backup` is 401 unsigned

### Cutover — on merge (in this order, automatically)
- [ ] `deploy.yml`: `api` to prod → rules → App Hosting (now calling `api`) → smoke tests
- [ ] Terraform staging, then prod (approval): triggers + scheduler created, old invoker bindings
      and Functions-only roles removed
- [ ] Verify on staging, then prod: upload an image → thumbnail + blurhash appear; submit the
      contact form → stored, email sent or the logged skip; run `nightly-backup` once → files in
      the backups bucket; Eventarc calls reach `/internal/*` (no 401/403 in the logs — if Eventarc
      signs for another URL, add it to `SERVICE_URL`)

### After the cutover
- [ ] Delete the 18 old functions in both projects (owner, or the agent with approval):
      `gcloud functions list --project <p>` → `gcloud functions delete <name> --region asia-south1 --project <p> --quiet`.
      Between the Terraform apply and this step both old and new triggers fire: processing is
      idempotent and the backup is a full export; a contact message in that window could email twice
- [ ] Delete Firebase's leftover scheduler job `firebase-schedule-nightly_backup-asia-south1` if
      the function deletion didn't
- [ ] Phase status → ✅

## Risks

| Risk | Handling |
|---|---|
| A bad image takes every endpoint down | Smoke test after each deploy; traffic back to the previous revision automatically; staging first |
| `/internal/*` exposed on a public service | `InternalCaller` checks signature, issuer, audience and the exact account; tested; unsigned is 401 in staging and prod |
| Eventarc signs for a URL not in `SERVICE_URL` | Seen on staging before the prod apply is approved; fix is one line in `backend/deploy/<project>.yaml` |
| `google-events` is unmaintained since 2024-12 | Round trip verified; a decode failure is a 422 that Eventarc retries; fallback is `protobuf` + the published `.proto` |
| Double triggers between apply and deletion | Only the contact email can repeat; keep the window short |
| New resource types 403 on first apply | The owner's one-time grants (Prerequisites) |

## Definition of done

- One Cloud Run service per project serves the site's reads, the admin, the contact form and the
  three background jobs; zero Cloud Functions remain
- `src/<domain>/<subdomain>/` unchanged, import-linter contracts passing
- A new endpoint is one route; a new subdomain is a folder plus two registrations, caught by a test
- `make dev` runs the API with `--reload`; VS Code debugs it directly
- CODE_FLOW, CLAUDE.md, rules, skills, RUNBOOK and decisions describe the new setup
