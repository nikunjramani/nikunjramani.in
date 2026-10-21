# Phase 9 · Backend on Cloud Run

**~12 hours over 4 PRs** · Status: 🟡 Proposed — awaiting the owner's review of
[ADR 0023](../../adr/0023-backend-as-one-cloud-run-service.md)

> **Goal:** the FastAPI backend runs as **one Cloud Run service** built from one image, with the
> domain/subdomain structure unchanged, Firestore unchanged, and no downtime on the way.

Why, and what was rejected: [ADR 0023](../../adr/0023-backend-as-one-cloud-run-service.md).
Database stays Firestore; PostgreSQL is a later, separate decision.

---

## The target, in one picture

```
Browser ──▶ App Hosting (Next.js) ── rewrite /api/v1/* ──┐
           Server Components ──── GET …/public ──────────┤
                                                         ▼
                                    Cloud Run service `api` (asia-south1, 1 vCPU, 1 GiB,
                                    concurrency 80, 0–3 instances, runs as api-runtime@)
                                    ├── /api/v1/<domain>/<sub>/…   public · AdminClaims · App Check
                                    └── /internal/…                Google OIDC token of events-invoker@ only
                                              ▲            ▲              ▲
             Eventarc: Storage object.finalized │  Eventarc: Firestore    │  Cloud Scheduler
             (media bucket) ────────────────────┘  contact_messages/*  ───┘  daily
                                                   document.created
                                    │
                                    ▼
                    Firestore · Cloud Storage · Firebase Auth · Secret Manager   (unchanged)
```

## The code layout

```
backend/                          ← renamed from backend/functions/ in PR 4
├── apps/
│   └── api.py                    create_app(): mounts every router — the one registration file
├── kernel/
│   ├── app.py                    NEW  make_app(): exception handlers, CORS, logging, /docs in dev
│   ├── events.py                 NEW  InternalCaller dependency (OIDC check) + CloudEvent parsing
│   ├── security.py · crud/ · audit.py · config.py · errors.py · firebase.py · logging.py
│   │   · records.py · timestamps.py                                            (unchanged)
│   ├── http.py                   DELETED (Firebase adapter)
│   └── wsgi_bridge.py            DELETED
├── src/<domain>/<subdomain>/     routes.py · schemas.py · service.py · repository.py   (unchanged)
│   ├── events.py                 NEW, only where a subdomain reacts to an event:
│   │                               media/processing  POST /internal/events/media-uploaded
│   │                               inbox/notifications POST /internal/events/contact-created
│   │                               ops/backup        POST /internal/jobs/backup
│   └── main.py                   DELETED (each existed only to deploy a function)
├── src/<domain>/main.py          DELETED (the FUNCTIONS tables)
├── main.py                       DELETED (FUNCTION_TARGET loader)
├── tests/                        mirrors src/ and kernel/, as now; + tests/apps/test_api.py
├── Dockerfile                    NEW  multi-stage: uv build stage (gcc for blurhash) → slim runtime,
│                                      non-root, `uvicorn apps.api:app --host 0.0.0.0 --port $PORT`
├── .dockerignore                 NEW
└── pyproject.toml                − firebase-functions, − a2wsgi, + uvicorn, + google-events;
                                    import-linter contracts unchanged, `apps` added as the top layer
```

**Rules that don't change:** domains never import each other; subdomains never import siblings;
no `common/`; no `__init__.py` outside `shared/generated`; tests only in `tests/`; content
subdomains subclass `kernel.crud`. **New rule:** `kernel/` and `src/` never import `apps/`;
`apps/api.py` is the only file that knows every subdomain.

**Registering a subdomain** goes from four places to two: its line in `apps/api.py` and its
route in `architecture/api-routes.json`. `tests/test_domain_registry.py` is rewritten to demand
that `src/*/*/routes.py`, `apps/api.py` and `api-routes.json` agree.

---

## Prerequisites

- [ ] Owner approves ADR 0023 (status → ✅ Accepted in PR 1)
- [ ] The pending prod Terraform apply from PR #19 is approved and applied — Phase 9 starts from a
      prod with no Terraform drift
- [ ] **Owner, once, before PR 2's first apply** — the Terraform apply identity needs to read and
      manage the three resource types PR 2 adds (lessons-learned 2026-10-16; `infra.md`). Run in
      PowerShell:
      ```powershell
      foreach ($p in 'nikunjramani-in-staging','nikunjramani-in') { foreach ($r in 'roles/artifactregistry.admin','roles/eventarc.admin','roles/cloudscheduler.admin') { gcloud projects add-iam-policy-binding $p --member="serviceAccount:github-terraform@$p.iam.gserviceaccount.com" --role=$r --condition=None } }
      ```
      PR 2 also adds them to `terraform_roles`, so Terraform records them afterwards.

---

## Tasks

### PR 1 · The app — code only, still deployed as Firebase functions (~4h)

Production keeps running the 18 functions; this PR adds the new entry point beside them and
proves it in tests and locally.

- [ ] ADR 0023 → ✅ Accepted; index row; this phase's status in `plan/README.md`
- [ ] `kernel/app.py` — `make_app(routers)`: the exception handler, CORS and logging setup moved
      out of `kernel/http.py` unchanged; `/docs` and `/openapi.json` only outside production
- [ ] `apps/api.py` — `create_app()`: `include_router(<sub>.routes.router, prefix="/api/v1/<domain>/<sub>")`
      for all 15 subdomains, plus the three `events.py` routers; `app = create_app()`
- [ ] `kernel/events.py`
  - `InternalCaller` dependency: requires `Authorization: Bearer <Google ID token>`; verifies with
    `google.oauth2.id_token.verify_oauth2_token` — signature, issuer `accounts.google.com`,
    audience = `SERVICE_URL`, `email_verified`, email = `events-invoker@<project>`. Anything else
    → 401/403 through `kernel.errors`. In `ENVIRONMENT=development` only, a missing token is
    allowed so events can be replayed locally
  - `parse_storage_event(request)` → bucket + object name (JSON `StorageObjectData`)
  - `parse_firestore_created(request)` → the new document as a dict, decoded from protobuf
    `DocumentEventData` (`google-events`), converted to plain Python values
- [ ] `events.py` per triggered subdomain — thin, like `routes.py`: parse → call the existing
      service → `204`. The services don't change. Eventarc retries any non-2xx, so a handler
      returns 2xx for "ignored" outcomes and lets real failures raise (retry is wanted)
      - `media/processing` → `ProcessingService().handle_upload(name, uploaded_by=…)` (already
        idempotent: skips an existing `media_assets/<id>`)
      - `inbox/notifications` → `notify_owner(data)` (at-least-once, as today)
      - `ops/backup` → `BackupService().export_all()`
- [ ] `kernel/config.py` — read the project from `GOOGLE_CLOUD_PROJECT` as well (Cloud Run doesn't
      set `GCLOUD_PROJECT`); add `service_url`; drop `runtime_service_account` once `main.py`'s
      `set_global_options` is the only user and is deleted in PR 4
- [ ] `Dockerfile` + `.dockerignore`; `uvicorn` and `google-events` added — **versions looked up
      on PyPI at the moment of pinning** (on 2026-10-21: uvicorn 0.54.0, google-events 0.14.0 —
      the latter's last release is 2024-12; confirm it still decodes current payloads, else
      decode with `protobuf` + the published `.proto`)
- [ ] Tests
  - `tests/apps/test_api.py`: every route in `api-routes.json` is mounted at its prefix; the old
    per-router tests run unchanged against routers (they never depended on the adapter)
  - `tests/kernel/test_events.py`: `InternalCaller` rejects no token, a wrong audience, a wrong
    email, an unverified email; accepts the right one (`verify_oauth2_token` patched, as
    `verify_id_token` is for admins); the development bypass works only in development
  - one test per `events.py`: a recorded Storage event and a Firestore protobuf event reach the
    service with the right arguments
- [ ] Local: `make dev` runs the Firestore/Auth/Storage emulators + `uvicorn --reload` on :8000
      + Next.js; `FUNCTIONS_BASE_URL` → `API_BASE_URL=http://127.0.0.1:8000`. Verified by hand:
      sign in, edit a project, upload an image and replay its event, submit the contact form
- [ ] Docs: `backend/functions/README.md` (how to run it), `.claude/rules/backend.md` (layout,
      the new rule), `add-api-endpoint` skill, CODE_FLOW §5 (local dev)

**Done when:** CI green; `docker build` works in CI; the image serves every route locally against
the emulators; production unchanged.

### PR 2 · Infrastructure + CI — the service runs beside the functions (~4h)

- [ ] Prerequisite grant above done by the owner
- [ ] `modules/iam`
  - `api-runtime@` — the roles `functions-runtime@` has today (Firestore user, storage objects,
    secret accessor, log writer, Firebase Auth admin) **minus** `eventarc.eventReceiver`; plus
    `serviceAccountTokenCreator` on itself for keyless signed upload URLs
  - `events-invoker@` — `roles/eventarc.eventReceiver`; Eventarc and Scheduler mint its tokens
  - `github-deploy@` — nothing new: its `deploy_roles` already include `run.admin`,
    `artifactregistry.repoAdmin` and `iam.serviceAccountUser`
  - `terraform_roles` + `artifactregistry.admin`, `eventarc.admin`, `cloudscheduler.admin`
  - existing service-agent bindings (`gcs-pubsub-publisher`, `pubsub-token-creator`) stay — they
    are what Storage and Firestore events need
- [ ] New `modules/api`
  - `google_artifact_registry_repository` `backend` (Docker, `asia-south1`) with a cleanup policy:
    keep the 10 newest images
  - `google_cloud_run_v2_service` `api` — runs as `api-runtime@`; 1 vCPU / 1 GiB; concurrency 80;
    min 0 / max 3; env `ENVIRONMENT`, `ALLOWED_ORIGINS`, `STORAGE_BUCKET`, `BACKUPS_BUCKET`,
    `MAIL_FROM`, `GOOGLE_CLOUD_PROJECT`, `SERVICE_URL`; secrets `RESEND_API_KEY` and
    `CONTACT_EMAIL_TO` from Secret Manager. Image starts as Google's placeholder
    (`us-docker.pkg.dev/cloudrun/container/hello`); `lifecycle.ignore_changes` on the image and
    client fields so CI's deploys aren't reverted
  - `allUsers` → `roles/run.invoker` (public, as the functions are)
  - **No event triggers or scheduler yet** — the functions still own those jobs; creating both
    would double-process (PR 3)
  - output `api_url`
- [ ] Values that were in `backend/functions/.env.<project>` move to each env's
      `terraform.tfvars` / module inputs (read from their source, never hard-coded in CI)
- [ ] CI: composite action `.github/actions/cloud-run-deploy` — auth (WIF) → `docker build` →
      push `asia-south1-docker.pkg.dev/<project>/backend/api:<sha>` → deploy the revision →
      smoke `GET /api/v1/ops/health` → on failure, route traffic back to the previous revision.
      Action versions **looked up live** when written. Wired into `pr.yml` (staging) and
      `deploy.yml` (prod) behind the same `functions` path filter; the Firebase functions deploy
      keeps running alongside until PR 4
- [ ] Order in a fresh project: Terraform creates the service on the placeholder → CI deploys the
      real image. In `deploy.yml` that's already the order for the second run onwards; the very
      first prod run is supervised (RUNBOOK note)
- [ ] Verify on staging: every `/api/v1/…/public` route returns what the matching function returns
      (same JSON); an admin call with a token works; `/internal/jobs/backup` is 401 without a
      token and 403 with a token for any other account
- [ ] Docs: `04-infrastructure.md`, RUNBOOK (deploy, rollback by revision, replaying an event),
      decisions IN-/CI- entries

**Done when:** `api` runs in both projects beside the functions, serving identical responses.

### PR 3 · Cutover — traffic and triggers move to `api` (~2h)

- [ ] Frontend: `lib/backend.ts` — `functionUrl(route)` becomes `apiUrl(route)` =
      `${API_BASE_URL}/api/v1/${route}`; `next.config.ts` keeps one rewrite,
      `/api/v1/:path*` → `${API_BASE_URL}/api/v1/:path*`; `apphosting*.yaml`:
      `FUNCTIONS_BASE_URL` → `API_BASE_URL` (the `api_url` output), BUILD and RUNTIME
- [ ] `modules/api` gains the triggers, all delivering as `events-invoker@` to `api`:
  - Eventarc `google.cloud.storage.object.v1.finalized` on the media bucket →
    `/internal/events/media-uploaded`
  - Eventarc `google.cloud.firestore.document.v1.created`, `document = contact_messages/{id}`,
    database `(default)`, location = the database's → `/internal/events/contact-created`
  - Cloud Scheduler daily → `/internal/jobs/backup`, OIDC audience = the service URL
- [ ] Between this apply and PR 4 both the old and new triggers fire. Image processing is
      idempotent and the backup is a full export, so that's harmless; a contact message in that
      window could email twice. PR 4 follows straight after
- [ ] Verify on staging, then prod: every page; admin sign-in, edit, publish; upload an image →
      `media_assets` doc appears with thumbnail and blurhash; contact form → message stored +
      email (or the logged skip while `RESEND_API_KEY` is the placeholder); trigger the scheduler
      job once → backup objects written
- [ ] Docs: CODE_FLOW §1 (system diagram), §3, §6–8; frontend rule (API calls); FE- entry

**Done when:** production serves every request and every event from `api`; the functions sit idle.

### PR 4 · Remove the functions (~2h)

- [ ] Delete the 18 deployed functions — `firebase functions:delete <names> --region asia-south1
      --force` per project, run by CI's deploy identity in a supervised step (or by the owner;
      the command goes in the PR)
- [ ] Code: delete `main.py`, `src/*/main.py`, `src/*/*/main.py`, `kernel/http.py`,
      `kernel/wsgi_bridge.py`, `requirements.txt`, `.env.<project>` files; `firebase-functions`
      and `a2wsgi` dependencies; `firebase.json` `functions` block and functions emulator;
      the second `venv/` from `make setup-backend`; `tests/test_main_entrypoint.py`
- [ ] Rename `backend/functions/` → `backend/`; update every path (Makefile, CI filters and
      actions, import-linter root, docs, `.claude/`)
- [ ] Terraform: delete `modules/functions` and `functions-runtime@` (`terraform state` handled by
      the module removal); the compute-default-SA `run.invoker`/`eventReceiver` bindings that
      only served Firebase triggers
- [ ] CI: drop the functions deploy path from `firebase-deploy`; `deploy.yml` rollback re-points
      to the previous Cloud Run revision
- [ ] Docs: ADR 0002, 0011 and 0017 status lines (superseded in part by 0023); CLAUDE.md
      (layout, rule 6, commands); `backend.md` rule (drop the Functions-only gotchas: a2wsgi,
      two Python environments, `FUNCTIONS` table, `FUNCTION_TARGET`); lessons-learned entries
      that no longer apply marked historical; decisions BE- entries superseded; this phase ✅

**Done when:** no Cloud Function exists in either project; `backend/` holds one app; every doc
describes it.

---

## Risks and how each is handled

| Risk | Handling |
|---|---|
| A bad image takes down every endpoint at once | CI smoke test after each deploy; automatic traffic rollback to the previous revision; staging first on every PR |
| `/internal/*` exposed on a public service | `InternalCaller` checks issuer, audience and the exact account; tested like `require_admin`; staging verifies 401/403 by hand in PR 2 |
| Firestore events are protobuf, and `google-events`' last release is 2024-12 | Verified in PR 1 with a real payload; fallback is decoding with `protobuf` and Google's published `.proto` |
| Double processing during cutover | Only the contact email can duplicate, only inside the PR 3 → PR 4 window, which is kept short |
| First apply 403s on new resource types | Owner's one-time grant (Prerequisites) before PR 2 |
| Cold start of one larger app is slower than one small function | Measured on staging in PR 2; `min_instances = 1` is the lever (a few dollars a month) |

## Definition of done

- One Cloud Run service per project serves the site's reads, the admin, the contact form and all
  three background jobs; zero Cloud Functions remain
- Code is still `src/<domain>/<subdomain>/`, with the same import-linter contracts passing
- A new endpoint is one route; a new subdomain is a folder plus two registrations, and a test
  catches a missing one
- `make dev` runs the API with `--reload` and a working debugger
- CODE_FLOW, CLAUDE.md, the rules, skills, RUNBOOK and decisions describe the new setup
