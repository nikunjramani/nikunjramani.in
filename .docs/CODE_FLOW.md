# Code flow

How a request, an edit, an upload, a schema change and a deploy actually move through this
repository — end to end, with the file each step lives in. Read top to bottom once; after that,
jump to the section you need.

*Why* each piece is shaped the way it is lives in [decisions/](./decisions/README.md) (code level)
and [adr/](./adr/README.md) (architecture). This file is kept true in the same PR as any change
that alters a flow (`.claude/rules/workflow.md`).

**Contents** — [1 The system](#1--the-system) · [2 Where code lives](#2--where-code-lives) ·
[3 A visitor reads a page](#3--a-visitor-reads-a-page) · [4 The admin signs in](#4--the-admin-signs-in) ·
[5 The admin edits content](#5--the-admin-edits-content) · [6 The contact form](#6--the-contact-form) ·
[7 Media](#7--media-upload-processing-library) · [8 Background jobs](#8--background-jobs) ·
[9 Inside one backend function](#9--inside-one-backend-function) ·
[10 Schemas and codegen](#10--schemas-and-codegen) · [11 Infrastructure](#11--infrastructure) ·
[12 CI/CD](#12--cicd) · [13 Local development](#13--local-development)

---

## 1 · The system

```
                         ┌──────────────────────────── Google Cloud project ─────────────────────────────┐
                         │  (two of them: nikunjramani-in = prod, nikunjramani-in-staging = PR previews)  │
 Browser                 │                                                                                 │
 ───────                 │   App Hosting (asia-southeast1)          Cloud Functions 2nd gen (asia-south1) │
 visitor ──GET page────────▶ Next.js 16 server ──Admin SDK read──▶ Firestore ◀──writes── api_<domain>_<sub>│
 admin  ──/api/v1/…────────▶   (rewrites /api/v1/<d>/<s>/* ───────────────────────────▶ FastAPI per fn    │
         ◀──Google sign-in──▶ Firebase Auth                                                │   │          │
         ──PUT signed URL────────────────────────────▶ GCS media bucket ──finalize──▶ on_media_uploaded   │
         ──App Check token── reCAPTCHA Enterprise                    contact_messages ──▶ on_contact_created ──▶ Resend
                         │                                            nightly ──▶ nightly_backup ──▶ GCS backups bucket
                         │   Secret Manager (RESEND_API_KEY, CONTACT_EMAIL_TO) → bound into functions          │
                         └─────────────────────────────────────────────────────────────────────────────────┘
```

Three rules shape every flow below:

- **Reads never touch Python.** Pages read Firestore directly from the Next.js server
  ([ADR 0005](./adr/0005-reads-bypass-python.md)).
- **Clients never write Firestore** — not even the admin. Every write is a Python API call
  ([ADR 0007](./adr/0007-deny-all-client-writes.md)).
- **One backend subdomain = one deployed function**, isolated from every other
  ([ADR 0017](./adr/0017-bounded-context-domains.md)).

---

## 2 · Where code lives

| Path | What |
|---|---|
| [architecture/schemas/](../architecture/schemas/) | JSON Schemas — every model, defined once |
| [architecture/api-routes.json](../architecture/api-routes.json) | the HTTP subdomains, `domain/sub` |
| [architecture/codegen/](../architecture/codegen/) | generators run by `make gen` |
| [frontend/src/app/(site)/](../frontend/src/app/%28site%29/) | public pages (Server Components) |
| [frontend/src/app/(admin)/admin/](../frontend/src/app/%28admin%29/admin/) | admin panel (`login/`, `(protected)/…`) |
| [frontend/src/app/api/admin/](../frontend/src/app/api/admin/) | the two Next.js route handlers: session cookie, media usage |
| [frontend/src/lib/data/](../frontend/src/lib/data/) | every Firestore **read** (server-only) |
| [frontend/src/lib/api/](../frontend/src/lib/api/) | every Python API **call** (admin, client-side) |
| [frontend/src/lib/firebase/](../frontend/src/lib/firebase/) | Admin SDK (server), client SDK (Auth), App Check |
| [frontend/src/generated/](../frontend/src/generated/) | TS types, Zod, admin form schemas, API routes — generated |
| [backend/functions/main.py](../backend/functions/main.py) | the one module Firebase loads |
| [backend/functions/src/\<domain\>/\<sub\>/](../backend/functions/src/) | one job each: `main → routes → schemas → service → repository` |
| [backend/functions/kernel/](../backend/functions/kernel/) | domain-free infrastructure: HTTP adapter, auth, audit, CRUD base |
| [backend/functions/shared/generated/](../backend/functions/shared/generated/) | Pydantic models — generated |
| [backend/functions/tests/](../backend/functions/tests/) | all backend tests |
| [infra/terraform/envs/{prod,staging}/](../infra/terraform/envs/) | one Terraform root per project |
| [infra/terraform/modules/](../infra/terraform/modules/) | project, iam, firestore, storage, secrets, functions, app-hosting, app-check, monitoring |
| [infra/rules/](../infra/rules/) | Firestore rules + indexes (partly generated); emulator-only storage rules |
| [.github/workflows/](../.github/workflows/) · [.github/actions/](../.github/actions/) | `pr.yml`, `deploy.yml` · composite actions |

---

## 3 · A visitor reads a page

```
GET /projects/acme-rebuild
  │
  ▼ App Hosting → Next.js server
frontend/src/app/(site)/layout.tsx            revalidate = 0 → rendered per request (ADR 0014)
  ├─ getProfile()                             lib/data/profile.ts       ─┐
  │                                                                       │ React.cache: one read
frontend/src/app/(site)/projects/[slug]/page.tsx                          │ per request, even if
  ├─ generateMetadata → getProjectBySlug(slug) lib/data/projects.ts      ─┤ called twice
  └─ Page            → getProjectBySlug(slug)                            ─┘
        │
        ▼ lib/firebase/admin.ts  db()          Admin SDK, ambient credentials (apphosting-runtime SA,
        │                                      Firestore *viewer* only)
        ▼ Firestore  projects/acme-rebuild
        │
        ▼ lib/data/convert.ts  fromSnapshot()  Timestamp → ISO string; id attached as `id`
        ▼ lib/data/projects.ts                 visibility must be public|unlisted, else null → 404;
                                               client.confidential → name + logo deleted HERE
  ▼
HTML with the real content (SEO: view-source shows it) + JSON-LD (components/site/json-ld.tsx)
```

- **Lists** (`/projects`, home) go through `listPublished()` in
  [lib/data/shared.ts](../frontend/src/lib/data/shared.ts):
  `where visibility == "public"` (+ optional equality filters) `orderBy order`. Each filter combination
  needs its composite index, declared in the schema (section 10).
- **Filters** on `/projects` live in the URL (`?kind=&tech=&status=`) —
  [components/site/project-filters.tsx](../frontend/src/components/site/project-filters.tsx) is the
  only client piece.
- **`unlisted`** projects render at their URL (with `noindex`) but `getAllProjects()` never returns
  them, so they're absent from lists and [sitemap.ts](../frontend/src/app/sitemap.ts).
- **Security headers** (HSTS, nosniff, frame DENY, …) come from
  [next.config.ts](../frontend/next.config.ts) `headers()`; staging adds `X-Robots-Tag: noindex`
  (`SITE_INDEXABLE=false`).
- **Images** are `next/image` from `storage.googleapis.com` (the media bucket's `public/` folder).

---

## 4 · The admin signs in

```
/admin/login  components/admin/sign-in-panel.tsx  (client)
  1. signInWithPopup(GoogleAuthProvider)                       Firebase Auth → ID token (1 h)
  2. POST /api/admin/session { idToken }                       app/api/admin/session/route.ts
        adminAuth().createSessionCookie(idToken, 5 days)       verifies the token first
        → Set-Cookie: session=…; HttpOnly; Secure; SameSite=Lax
  3. getIdTokenResult().claims.admin !== true ?
        → DELETE /api/admin/session + signOut → "not an admin" message (no redirect loop)
  4. router.push("/admin")

Every later request to /admin/*:
  src/proxy.ts                         cookie *present*? no → redirect /admin/login   (cheap, no crypto)
  (admin)/admin/(protected)/layout.tsx getAdminSession() → verifySessionCookie(cookie, checkRevoked=true)
                                       invalid → redirect /admin/login
                                       valid but no admin claim → explicit refusal page
                                       admin → <AdminShell>
```

The cookie only gates **page navigation**. API calls carry their own token (section 5), and the
Python API re-verifies everything — the frontend gates are convenience, not security
([03-security.md](./plan/03-security.md)).

Admin access is granted with the `admin: true` custom claim — by
[infra/scripts/set_admin_claim.py](../infra/scripts/set_admin_claim.py) the first time, then from
the panel's **Access** page (`api_identity_admins`, section 9).

---

## 5 · The admin edits content

Example: editing a skill on `/admin/skills`.

```
BROWSER  components/admin/content-collection-screen.tsx
  ├─ list:  useRecordList → lib/api/content.ts → apiFetch("GET /content/skills/")
  └─ save:  <RecordFormDialog> → <SchemaForm> (generated admin schema + Zod, drafts in localStorage)
            toMergePatch(original, edited)      lib/merge-patch.ts — a cleared field becomes null
            apiFetch("PATCH /content/skills/<id>", patch)
  lib/api/client.ts
     auth().authStateReady() → currentUser.getIdToken()   fresh token, refreshed by the SDK
     fetch("/api/v1/content/skills/<id>", Authorization: Bearer <token>)
     401 → hard navigation to /admin/login;  !ok → ApiError(message from {"error":{…}})
        │
        ▼ same origin, no CORS
NEXT.JS  next.config.ts rewrites()  /api/v1/content/skills/:path* → $FUNCTIONS_BASE_URL/api_content_skills/:path*
        │                           (routes generated from architecture/api-routes.json)
        ▼
CLOUD RUN  api-content-skills (allUsers invoker — auth is in-process)
        ▼
PYTHON   main.py → FUNCTION_TARGET=api_content_skills → imports only src/content/skills/main.py
         kernel/http.py make_function → Flask request → kernel/wsgi_bridge.py → FastAPI app
         src/content/skills/routes.py   update_skills(doc_id, patch, claims: AdminClaims, service)
            AdminClaims = kernel/security.py require_admin:
               verify_id_token (401 if missing/invalid) → claims["admin"] is True (403 otherwise)
         src/content/skills/service.py  SkillService(CrudService[Skill]).patch
            kernel/crud/service.py:
              - drop client-sent `audit`; refuse a slug change (slug = doc id = URL)
              - RFC 7386 deep_merge(before, patch)
              - visibility change → action publish | unpublish | update; stamp audit.updatedAt
                (+ publishedAt on first publish)
              - validate against the generated Skill model → 422 on failure
         src/content/skills/repository.py  SkillRepository(BaseRepository[Skill]).save
              kernel/timestamps.py to_firestore()   ISO strings → datetimes
              Firestore skills/<id>.set(...)
         kernel/audit.py AuditWriter.record → audit_log/<auto>  {actor, action, collection, docId, before, after, at}
        ▼
         RecordOut {id, data} → JSON → browser updates the list
NEXT VISIT to the public page reads Firestore fresh (section 3) — no cache to invalidate.
```

- **Create** = `POST /`, **delete** = `DELETE /{id}`, **reorder** = `POST /reorder` (assigns `order` =
  0..n-1 in one batch). **Singletons** (`profile/main`, `site_config/main`) are `GET /`, `PUT /`
  (full replace, `CrudService.upsert`) and `PATCH /` on their one fixed document. **Projects** add
  `POST /{id}/duplicate` (fresh `-copy` slug, reset to draft).
- **Errors**: services raise [kernel/errors.py](../backend/functions/kernel/errors.py) exceptions;
  [kernel/http.py](../backend/functions/kernel/http.py) turns them into
  `{"error": {"code", "message"}}` with the right status; `client.ts` shows `message`.
- The **audit trail** shows inside each record's editor
  ([components/admin/audit-trail.tsx](../frontend/src/components/admin/audit-trail.tsx)), read via
  `api_ops_audit` — newest first, filtered by collection and document, 50 entries.

---

## 6 · The contact form

```
BROWSER  /contact  components/site/contact-form.tsx (client)
  initAppCheck() early     lib/firebase/app-check.ts — lazy-imports the SDK; reCAPTCHA Enterprise
                           scores the visitor invisibly (no-op in local dev: no site key)
  submit → getAppCheckToken() → lib/contact.ts submitContact()
           POST /api/v1/inbox/contact  {name, email, subject?, message, honeypot}
                X-Firebase-AppCheck: <token>
        ▼ rewrite → api_inbox_contact (public)
PYTHON   src/inbox/contact/routes.py  ContactRequest validated (length caps → honest 422s)
         client IP = first X-Forwarded-For hop (best effort)
         src/inbox/contact/service.py ContactService.submit — every failure below is SILENT (202 anyway):
           1. honeypot filled?                          → drop
           2. app_check.verify_app_check(token)         → invalid/missing in prod → drop (fails closed)
           3. rate_limit.RateLimiter (Firestore transaction on _rate_limits/<scope>_<id>_<window>):
                3/hour per IP, 20/hour global            → over → drop
           4. spam.score_spam(message)                  → 0..1, flags only
           5. NewMessageRepository.create → contact_messages/<auto>  (expiresAt = +2 years, TTL)
         → 202 {"ok": true, "message": "Thanks — …"}
        ▼ Firestore onCreate
TRIGGER  src/inbox/notifications/main.py on_contact_created (secrets: CONTACT_EMAIL_TO, RESEND_API_KEY)
           service.render_email → every visitor value HTML-escaped; spam ≥ 0.5 flagged in the body
           email.send_email → Resend API, 2 retries;  key empty/whitespace → log + skip
ADMIN    /admin/messages → api_inbox_messages: list (null-safe newest-first), mark read/replied,
         delete, CSV export (formula-injection-safe), all audited
```

App Check runs **before** the rate limiter so unverified traffic can't burn the global window and
block real visitors ([ADR 0020](./adr/0020-app-check-replaces-turnstile.md)). Rate-limit window
documents and messages expire through Firestore TTL policies on `expiresAt`.

---

## 7 · Media: upload, processing, library

```
1 · ASK    admin /admin/media  components/admin/media/upload-zone.tsx
           lib/api/media.ts requestUploadUrl(type, size) → POST /media/upload
           src/media/upload/service.py  validate (webp/jpeg/png/gif, ≤ 20 MiB)
                                        path = uploads/media/<uuid32>/original.<ext>
           src/media/upload/storage.py  v4 signed PUT URL, 15 min, signed via IAM signBlob as the
                                        runtime SA (no key file)
2 · PUT    browser → uploadToSignedUrl → GCS  <project>-media/uploads/media/<id>/original.<ext>
           (private prefix; may still carry EXIF/GPS)
3 · PROCESS  GCS finalize event → src/media/processing/main.py on_media_uploaded (1 GiB, ≤ 2 instances)
           service.handle_upload:
             path doesn't match UPLOAD_PATTERN → ignore (its own outputs never re-trigger it)
             media_assets/<id> already exists  → ignore (events are at-least-once)
             image.process_image: EXIF-rotate → RGB → WebP q82 + 400px thumbnail + blurhash 4×3
             upload  public/media/<id>/processed.webp, public/media/<id>/thumbnail.webp
             create  media_assets/<id> {url, thumbnailUrl, width, height, blurhash, …}
4 · USE    admin picks the asset in a schema form's media field; public pages render the WebP with
           its blurhash placeholder (lib/blurhash.ts). public/ is world-readable through a managed
           folder IAM binding; nothing else in the bucket is.
5 · MANAGE /media/library: list, set alt text/caption (required before an asset can be picked),
           delete → best-effort delete of all three objects, then the document; audited.
           "Where is this used?" is a Next.js read, not Python:
           app/api/admin/media/[id]/usage/route.ts → lib/data/media-usage.ts (session-cookie authorised)
```

`uploadedBy` is read from the object's metadata if present; the admin client doesn't set it today.

---

## 8 · Background jobs

| Function | Trigger | Does | Code |
|---|---|---|---|
| `on_contact_created` | Firestore create on `contact_messages/{id}` | emails the owner | [src/inbox/notifications/](../backend/functions/src/inbox/notifications/) |
| `on_media_uploaded` | GCS object finalized in the media bucket | WebP + thumbnail + blurhash → `media_assets` | [src/media/processing/](../backend/functions/src/media/processing/) |
| `nightly_backup` | Cloud Scheduler, every 24 h | every collection in `BACKED_UP_COLLECTIONS` → `<project>-backups/<timestamp>/<collection>.json` | [src/ops/backup/](../backend/functions/src/ops/backup/) |

Monitoring ([modules/monitoring](../infra/terraform/modules/monitoring/main.tf)): an uptime check on
`/api/v1/ops/health`, a log-based function-error metric, and email alerts for both.

---

## 9 · Inside one backend function

```
firebase deploy discovers:      backend/functions/main.py (FUNCTION_TARGET unset → imports every subdomain)
a deployed instance cold-starts: FUNCTION_TARGET=api_content_projects
                                 → main.py imports ONLY src/content/projects/main.py
                                   (one function's cold start never builds another's app)

main.py                      set_global_options(service_account=functions-runtime@…, max_instances=3)
                             FUNCTIONS = {**content, **identity, **inbox, **media, **ops}
src/<domain>/main.py         FUNCTIONS = {"api_<domain>_<sub>": "src.<domain>.<sub>.main", …}   (no imports)
src/<domain>/<sub>/main.py   api_<domain>_<sub> = make_function(router, name="api_<domain>_<sub>")
kernel/http.py make_function make_app: FastAPI (/docs off in prod), CORS allowlist, DomainError handler
                             wsgi_from_asgi(app) → a fresh asyncio.run() per request (no thread to die on fork)
                             _handler.__name__ = name BEFORE https_fn.on_request (the SDK names the
                             deployed function from it)
```

| Domain | Subdomains → functions |
|---|---|
| content | profile, projects, skills, experience, education, certifications, posts, settings → `api_content_*` |
| media | upload → `api_media_upload` · processing → `on_media_uploaded` · library → `api_media_library` |
| inbox | contact → `api_inbox_contact` (public) · messages → `api_inbox_messages` · notifications → `on_contact_created` |
| ops | health → `api_ops_health` (public) · audit → `api_ops_audit` · backup → `nightly_backup` |
| identity | admins → `api_identity_admins` (list / grant / revoke the admin claim) |

Layering inside a subdomain is one way — `main → routes → schemas → service → repository` —
enforced by import-linter ([pyproject.toml](../backend/functions/pyproject.toml)) and
`tests/test_import_rules.py`. Registration (four places) is checked by
`tests/test_domain_registry.py`; see [backend/functions/README.md](../backend/functions/README.md).

---

## 10 · Schemas and codegen

```
architecture/schemas/*.schema.json   (+ enums/, common/, x-firestore: collection, publicRead, indexes, ttlField)
architecture/api-routes.json
        │  make gen → architecture/codegen/generate.sh
        ├─ datamodel-codegen      → backend/functions/shared/generated/*.py  (+ curated __init__.py)
        ├─ gen-frontend.mjs       → frontend/src/generated/types.ts, schemas.zod.ts,
        │                           admin-schemas.ts (drives <SchemaForm>), api-routes.ts (drives rewrites)
        ├─ gen-indexes.py         → infra/rules/firestore.indexes.json (composite indexes + TTL overrides)
        ├─ gen-rules.py           → infra/rules/firestore.rules (the generated public-read block)
        └─ gen-docs.py            → architecture/docs/ERD.md
make validate → validate.py: every schema compiles; examples/valid pass; examples/invalid fail
CI (schema-check action): validate + gen, then `git diff --exit-code` — any drift fails the PR
```

Adding a field: edit the schema → `make gen` → it appears in the Pydantic model, the TS type, the
Zod validator and the admin form with no hand edits (`add-schema-field` skill).

---

## 11 · Infrastructure

```
infra/terraform/envs/prod     ─┐  same modules, different tfvars + GitHub environments
infra/terraform/envs/staging  ─┘  state: GCS bucket <project>-tfstate
   modules/project      APIs + monthly billing budget
   modules/iam          runtime SAs (functions-runtime: Firestore user, storage objects, secrets,
                        Auth admin for the claim, Eventarc receiver; apphosting-runtime: Firestore
                        viewer, no writes) + CI identities via WIF:
                        github-plan (read, PRs) · github-deploy (env: staging|production)
                        · github-terraform (env: staging-infra|production-infra)
   modules/firestore    database + TTL fields (contact_messages, _rate_limits)
   modules/storage      <project>-media (versioned, CORS for signed PUTs, public/ managed folder)
                        <project>-backups (30-day lifecycle)
   modules/secrets      secret containers + accessor bindings (values added by hand)
   modules/functions    allUsers invoker on every HTTP function (needs them deployed first)
   modules/app-hosting  web app, App Hosting backend, apex + www domains
   modules/app-check    reCAPTCHA Enterprise SCORE key + App Check registration
   modules/monitoring   uptime check, error metric, alerts
```

What Terraform doesn't own: function code and runtime limits (the Python decorators,
`firebase deploy`), Firestore rules/indexes (`firebase deploy`), secret values (by hand), the
first admin claim (`set_admin_claim.py`), and bootstrap roles on the billing account
([04-infrastructure.md](./plan/04-infrastructure.md)).

---

## 12 · CI/CD

```
PULL REQUEST  .github/workflows/pr.yml
  changes (dorny/paths-filter, markdown excluded) ─┬─ schemas   → actions/schema-check
                                                   ├─ backend   → actions/backend-checks (ruff, mypy, import-linter,
                                                   │                pytest under the Firestore emulator)
                                                   ├─ frontend  → actions/frontend-checks (typegen, tsc, eslint,
                                                   │                vitest, next build with apphosting.yaml env)
                                                   └─ infra-plan (prod + staging) → actions/terraform-plan
                                                                    (fmt, plan as github-plan, plan posted on the PR)
  checks   ← the one required status: every job succeeded or was skipped
  preview  (same-repo PRs, after checks, only touched targets) → actions/firebase-deploy
             project=staging · rules / functions / apphosting · retried 3× · smoke test
           → Lighthouse (report only) → sticky PR comment with the staging URL

MERGE TO MAIN  .github/workflows/deploy.yml   (only if vars.PROD_DEPLOY_ENABLED == "true")
  changes  (same filters, diffed against the previous main)
  deploy   environment=production → actions/firebase-deploy project=default, touched targets only,
           smoke test /  and /api/v1/ops/health
  rollback if deploy failed: check out the previous commit, deploy everything with the current action
  terraform if infra/terraform changed (or manual infra_only):
           staging-infra apply → production-infra apply (waits for the owner's approval)
```

- Docs-only changes (`.docs/`, `.claude/`, any `*.md`) run only `changes` + `checks`; deploy nothing.
- A `.github/**` change runs everything.
- Project IDs come from `.firebaserc` aliases; site URLs, WIF provider and service accounts from
  GitHub environment variables; frontend env from `frontend/apphosting*.yaml`.
- Details and the "what runs for what" table: [RUNBOOK](./RUNBOOK.md#cicd-and-staging).

---

## 13 · Local development

```
make setup   uv venv + venv/ + requirements.txt (backend) · npm install (frontend)
make dev     firebase emulators (auth 9099, functions 5001, firestore 8080, storage 9199, UI 4040)
             + next dev on :3000 — rewrites point at the functions emulator
make gen     after any schema change
make lint    ruff · mypy --strict · import-linter · tsc · eslint · terraform fmt
make test    pytest (emulator-backed tests skip without the emulator) · vitest
```

Debug one function with `functions-framework` (VS Code "Backend: debug a subdomain"), not through
the functions emulator — [RUNBOOK](./RUNBOOK.md#debugging-vs-code).
