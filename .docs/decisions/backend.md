# Backend decisions

Python 3.13 · FastAPI · Cloud Functions for Firebase 2nd gen. Root:
[backend/functions/](../../backend/functions/). Flow: [CODE_FLOW §5–9](../CODE_FLOW.md#5--the-admin-edits-content).
Entries BE-01…BE-38 were backfilled on 2026-10-16 from the code and its history.

## Entry points and the HTTP adapter

### BE-01 · The deployed function's `__name__` is set before decorating it

- **Where:** [kernel/http.py](../../backend/functions/kernel/http.py) — `make_function`
- **Decision:** `_handler.__name__ = name` (and `__qualname__`) before `https_fn.on_request(...)` is applied.
- **Why:** the Firebase SDK derives the deployed function's name from the handler's `__name__` at
  decoration time. Without this every subdomain deployed as `handler` and collided.
- **Outcome:** one adapter serves every subdomain. Cost: a non-obvious ordering constraint, documented in the module docstring.
- **Related:** ADR 0011, ADR 0017

### BE-02 · A hand-written ASGI→WSGI bridge instead of `a2wsgi.ASGIMiddleware`

- **Where:** [kernel/wsgi_bridge.py](../../backend/functions/kernel/wsgi_bridge.py) — `wsgi_from_asgi`
- **Decision:** each WSGI call runs the FastAPI app in a fresh `asyncio.run()`; only a2wsgi's pure
  `build_scope` helper is reused.
- **Why:** `ASGIMiddleware` starts a background event-loop thread at construction. Werkzeug's
  reloader and the functions runtime fork; a forked child has no copy of that thread, so every
  request waited on it forever. Reproduced with a bare `os.fork()`.
- **Outcome:** no hang. Cost: a new event loop per request — irrelevant for a function serving
  one request at a time. Type-checked and unit-tested code hid this; only the emulator showed it.
- **Related:** ADR 0003 (implementation note), lessons-learned

### BE-03 · The root `main.py` imports only the module `FUNCTION_TARGET` names

- **Where:** [main.py](../../backend/functions/main.py)
- **Decision:** merge every domain's `FUNCTIONS` table; when `FUNCTION_TARGET` is set (inside a
  deployed instance) import only that function's subdomain module; when unset (deploy discovery,
  emulator, pytest) import all.
- **Why:** cold start time scales with imports. Without this, every function's cold start built
  every other subdomain's FastAPI app.
- **Outcome:** one subdomain's cold start loads one subdomain. Cost: functions must be registered
  in a table, not just defined — BE-04.
- **Related:** ADR 0017

### BE-04 · Three levels of entry point, checked by tests

- **Where:** `main.py` → `src/<domain>/main.py` (`FUNCTIONS` dict, no imports) → `src/<domain>/<sub>/main.py`
- **Decision:** the subdomain defines its function; the domain lists it by name and module path;
  the root merges. `tests/test_main_entrypoint.py` imports the real `main.py` and cross-checks
  every function, secret and instance limit; `tests/test_domain_registry.py` checks the four
  registrations (FUNCTIONS, `api-routes.json`, import-linter contracts, Terraform `http_functions`).
- **Why:** each registration, when missed, fails *silently in production* — a function that never
  deploys, a 404 rewrite, a 403 at Cloud Run.
- **Outcome:** forgetting one fails `make test` instead.
- **Related:** ADR 0017, SC-04

### BE-05 · No `__init__.py`; mypy `explicit_package_bases`; pytest `importlib` mode

- **Where:** [pyproject.toml](../../backend/functions/pyproject.toml)
- **Decision:** implicit namespace packages everywhere except `shared/generated` (whose generated
  `__init__.py` is the curated re-export).
- **Why:** the owner asked to drop boilerplate `__init__.py` files. With them gone, many files share
  names (`main.py`, `service.py`), so mypy needs module names from paths and pytest needs
  `--import-mode=importlib`.
- **Outcome:** less noise. Cost: two tool settings that look odd until you know why.
- **Related:** ADR 0017, lessons-learned (2026-10-13)

## Structure and layering

### BE-06 · Subdomains own their slice — even when two slices look alike

- **Where:** `src/media/{upload,processing,library}/paths.py`; `tests/media/test_layout.py`
- **Decision:** no `common/` folder and no sibling imports. Where subdomains share a convention
  (the bucket layout), each spells out the part it uses, and a test pins all three to one contract.
- **Why:** a shared folder became the place every job's code went (the 2026-10-13 rewrite). Small
  duplication is cheaper than coupling three deployables.
- **Outcome:** subdomains deploy and change independently. Cost: a few duplicated lines, guarded by a test.
- **Related:** ADR 0017

### BE-07 · One-way layers; only repositories touch Firestore

- **Where:** import-linter `layers` contract; `tests/test_import_rules.py`
- **Decision:** `main → routes → schemas → service → repository`. Routes do HTTP only; services hold
  rules and know no HTTP; repositories are the only Firestore SDK users. The one exception is
  `inbox/contact/rate_limit.py`, whose check-and-increment must be a single transaction.
- **Why:** services stay unit-testable with a faked repository; HTTP and storage concerns can't leak.
- **Outcome:** enforced by `make lint`, not review. Cost: a thin repository class even for one call.
- **Related:** ADR 0016 (superseded structure), ADR 0017

### BE-08 · Services raise `kernel.errors`; one handler turns them into JSON

- **Where:** [kernel/errors.py](../../backend/functions/kernel/errors.py), `make_app` in kernel/http.py
- **Decision:** `DomainError` subclasses carry `status_code` and `code`; the app's exception handler
  returns `{"error": {"code", "message"}}`.
- **Why:** services must not import HTTP concepts (BE-07), yet each failure needs a precise status.
- **Outcome:** one error shape the frontend parses (`admin/api-client/client.ts`).

### BE-09 · Generic content CRUD lives once in `kernel.crud`; routes stay written out

- **Where:** [kernel/crud/](../../backend/functions/kernel/crud/) — `BaseRepository`, `CrudService`, `RecordOut`
- **Decision:** audit stamps, publish transitions, merge-patch and reorder are implemented once and
  subclassed per collection; each subdomain still writes its own `routes.py`.
- **Why:** the rules are identical for every visibility/order collection; a route factory (ADR 0016)
  hid the HTTP surface and was replaced. Written-out routes are greppable and individually changeable.
- **Outcome:** a new collection is ~40 lines. Cost: route files that look repetitive on purpose.
- **Related:** ADR 0012, ADR 0016, ADR 0017

### BE-10 · Updates are RFC 7386 merge patches; `slug` and `audit` are protected

- **Where:** `CrudService.patch`, `deep_merge` in [kernel/crud/service.py](../../backend/functions/kernel/crud/service.py)
- **Decision:** `null` deletes a key, objects merge, lists replace. A client-sent `audit` is dropped
  (server-owned); changing `slug` is a 422.
- **Why:** a form sending its values can't clear a field (`undefined` disappears in JSON); merge
  patch can. The slug is the document id *and* the public URL — renaming it would orphan both.
- **Outcome:** partial saves that can clear fields. Pairs with FE-11 on the client.

### BE-11 · Publish/unpublish is derived from the visibility change

- **Where:** `_transition` and `CrudService.patch`/`upsert`
- **Decision:** the audit action is `publish` / `unpublish` / `update` depending on how `visibility`
  moved; the first publish stamps `publishedAt`, which survives later replaces.
- **Why:** the audit trail should say *what happened*, and a re-publish must not reset the original date.

### BE-12 · Repositories return `Record[T]` — the id travels beside the model

- **Where:** [kernel/records.py](../../backend/functions/kernel/records.py)
- **Decision:** `Record(id, data)` rather than an `id` field on the model.
- **Why:** every schema sets `additionalProperties: false` and has no `id`; injecting one fails validation.
- **Related:** SC-02, FE-06 (`WithId` on the frontend)

### BE-13 · Timestamps cross the Firestore boundary in exactly one module, matched strictly

- **Where:** [kernel/timestamps.py](../../backend/functions/kernel/timestamps.py)
- **Decision:** `to_firestore` / `from_firestore` walk the document; only strings matching a full
  date-*time* (`YYYY-MM-DDTHH:MM`) become datetimes.
- **Why:** schemas store ISO strings, Firestore stores Timestamps. A looser match corrupted valid
  content — the slug `20210601` and `2021-W01` both parse as dates.
- **Outcome:** nothing else knows Firestore's type exists.

### BE-14 · `list_all(order_by=None)` + a null-safe sort for the inbox

- **Where:** `BaseRepository.list_all`; `MessageService._sorted`
- **Decision:** contact messages are fetched unordered and sorted in Python with a null-safe key.
- **Why:** Firestore's `order_by(field)` silently drops documents missing that field; a message
  hidden from the inbox is worse than one sorted imperfectly.

## Auth and audit

### BE-15 · `ensure_app()` runs before verifying a token

- **Where:** `verify_token` in [kernel/security.py](../../backend/functions/kernel/security.py); [kernel/firebase.py](../../backend/functions/kernel/firebase.py)
- **Decision:** initialise the Admin SDK app explicitly before `verify_id_token`.
- **Why:** on a cold instance token verification is the first SDK call; without an app it raised
  "default app does not exist", caught by the broad `except` and reported as an invalid token —
  possibly forever. Every unit test mocked `verify_id_token`, so only the emulator found it.
- **Related:** lessons-learned

### BE-16 · Every admin route verifies the token *and* the `admin` claim, every request

- **Where:** `require_admin` / `AdminClaims` in kernel/security.py
- **Decision:** a missing or bad token is 401; a valid token without `admin: true` is 403. No session
  cache. The verified claims are passed on, so routes use them for the audit actor without re-verifying.
- **Why:** signing in with Google is open to anyone; the custom claim (settable only server-side)
  is the authorisation. The frontend's gates are convenience (FE-08).
- **Related:** ADR 0007, plan/03-security.md

### BE-17 · Audit entries keep explicit `null`s

- **Where:** [kernel/audit.py](../../backend/functions/kernel/audit.py)
- **Decision:** `before` on a create and `after` on a delete are stored as `null`, not omitted.
- **Why:** an explicit null reads differently from a missing key to anyone inspecting the trail.

## Contact form (inbox)

### BE-18 · Every anti-abuse check fails silently; field validation stays honest

- **Where:** [src/inbox/contact/service.py](../../backend/functions/src/inbox/contact/service.py)
- **Decision:** honeypot, App Check, rate limit — any trip returns the same 202 success. Malformed
  fields (too long, missing) still get a 422 from Pydantic.
- **Why:** telling a bot which check fired helps it tune; a real visitor benefits from field errors.
- **Outcome:** cost: a genuine sender who trips a false positive (a shared IP) is never told. Acceptable
  for a low-volume personal form, not for a support channel.

### BE-19 · App Check is verified before the rate limiter

- **Where:** `ContactService.submit`
- **Decision:** order is honeypot → App Check → rate limit → store.
- **Why:** counting unverified requests let anyone exhaust the 20/hour global window with a curl
  loop and silently block every real visitor (found in the 2026-10-13 review).
- **Related:** ADR 0020

### BE-20 · Rate limits are fixed windows in a Firestore transaction

- **Where:** [src/inbox/contact/rate_limit.py](../../backend/functions/src/inbox/contact/rate_limit.py)
- **Decision:** a document per scope/identifier/window start; read-check-write in one transaction;
  `expiresAt` = two windows ahead, deleted by a TTL policy.
- **Why:** `Increment()` can't express "reject if over"; two concurrent requests at count 4 of 5 must
  not both pass. Window ids make new windows free; TTL keeps old ones from piling up.
- **Outcome:** 3/hour per IP, 20/hour global. Cost: the one sanctioned Firestore call outside a repository.

### BE-21 · The request model is narrower than the stored model

- **Where:** [src/inbox/contact/schemas.py](../../backend/functions/src/inbox/contact/schemas.py) — `ContactRequest`
- **Decision:** the body accepts only name, email, subject, message, honeypot; ip, userAgent,
  spamScore, read flags and timestamps are set server-side.
- **Why:** accepting the full `ContactMessage` would let a POST forge its own metadata.

### BE-22 · Client IP is the first `X-Forwarded-For` hop, used only for a best-effort limit

- **Where:** `_client_ip` in contact/routes.py
- **Why:** behind Google's front end and the Next.js rewrite, that hop is the visitor — but a client
  can send its own header, so the per-IP limit is advisory. App Check is the real gate.

### BE-23 · Spam is scored, never blocked — three cheap signals

- **Where:** [src/inbox/contact/spam.py](../../backend/functions/src/inbox/contact/spam.py)
- **Decision:** links, all-caps ratio, character runs → 0..1; the notification flags ≥ 0.5.
- **Why:** this form gets little traffic; a model tuned against traffic that doesn't exist is
  premature, and a false positive should still reach the inbox.

### BE-24 · The owner's email is sent by a Firestore trigger, not the request

- **Where:** [src/inbox/notifications/](../../backend/functions/src/inbox/notifications/) — `on_contact_created`
- **Decision:** the API only persists; `on_document_created` renders and sends via Resend, with two
  retries. Every visitor value is HTML-escaped.
- **Why:** the visitor's request stays fast and doesn't fail when the mail provider does; the email
  body is untrusted input landing in the owner's inbox.

### BE-25 · An empty or whitespace mail key means "not configured" — skip, don't fail

- **Where:** [src/inbox/notifications/settings.py](../../backend/functions/src/inbox/notifications/settings.py) (`str_strip_whitespace=True`), `send_email`
- **Decision:** a blank `RESEND_API_KEY` logs a warning and skips sending.
- **Why:** a bound secret must have a version before deploy, and Secret Manager rejects empty
  versions — so an unconfigured key is a single newline, which stripping turns into "empty".
- **Outcome:** messages are still stored (and visible in the admin inbox) until email is set up.
- **Since:** 2026-10-16 · **Related:** lessons-learned, RUNBOOK "Contact form keys"

## Media

### BE-26 · Uploads go straight to Storage on a short-lived signed URL

- **Where:** [src/media/upload/](../../backend/functions/src/media/upload/)
- **Decision:** the API validates type (webp/jpeg/png/gif) and size (≤ 20 MiB) and returns a v4
  signed PUT URL valid 15 minutes, signed through IAM `signBlob` as the runtime service account.
- **Why:** large files never pass through a 256 MB function; no key file exists to sign with.
- **Outcome:** signing only works for a deployed service account, so it's unit-tested with signing mocked.

### BE-27 · Raw uploads are private; derivatives are public; the trigger can't re-trigger itself

- **Where:** `src/media/*/paths.py`, [processing/service.py](../../backend/functions/src/media/processing/service.py)
- **Decision:** raw files land in `uploads/media/<id>/original.<ext>`; WebP derivatives in
  `public/media/<id>/`. The trigger acts only on paths matching `UPLOAD_PATTERN` and stops if
  `media_assets/<id>` already exists.
- **Why:** originals can carry EXIF/GPS; the trigger fires on its own writes too; Storage events
  are at-least-once.

### BE-28 · Images are EXIF-rotated, then re-encoded (which strips EXIF)

- **Where:** [processing/image.py](../../backend/functions/src/media/processing/image.py)
- **Decision:** `exif_transpose`, convert to RGB(A), WebP q82, a 400 px thumbnail, a 4×3 blurhash from
  a 100 px sample. Pure functions over bytes.
- **Why:** phones store orientation in EXIF; the re-encoded WebP carries none, so rotate first.
  Pure functions test without any bucket.

### BE-29 · Deleting an asset removes its files best-effort, then the document

- **Where:** `LibraryService.delete`
- **Why:** an orphaned blob costs a few KB; a document pointing at nothing breaks pages.

### ~~BE-30~~ Superseded by [BE-39](#be-39--the-media-library-answers-where-is-this-image-used-and-delete-enforces-it) · "Where is this image used?" is answered by Next.js, not Python

- **Where:** `frontend/src/app/(admin)/api/admin/media/[id]/usage/route.ts`
- **Why:** it reads other domains' collections; reads belong in Next.js (ADR 0005) and the media
  domain must not import content (ADR 0017).

## Ops and identity

### BE-31 · Backups are per-document JSON, not GCP's native export

- **Where:** [src/ops/backup/service.py](../../backend/functions/src/ops/backup/service.py)
- **Decision:** a daily job writes each collection in `BACKED_UP_COLLECTIONS` to the backups bucket.
  A test checks the list covers every collection the schemas declare.
- **Why:** a backup must be restorable into the *emulator* for verification first; the native
  format only imports into real Firestore. Rate-limit windows are deliberately excluded.

### BE-32 · Admin revocation refuses self-removal and removing the last admin

- **Where:** [src/identity/admins/service.py](../../backend/functions/src/identity/admins/service.py)
- **Decision:** revoke also revokes the user's refresh tokens; grant takes effect at next sign-in.
- **Why:** locking the only owner out of their own panel has no recovery path short of a script;
  revoking sessions makes a removal immediate (the panel checks `checkRevoked`).

### BE-33 · CSV export neutralises spreadsheet formulas

- **Where:** `csv_safe` in [src/inbox/messages/service.py](../../backend/functions/src/inbox/messages/service.py)
- **Why:** every text column comes from the public form; a cell starting `=`, `+`, `-`, `@` would run
  as a formula in Excel/Sheets.

## Configuration and runtime

### BE-34 · `/docs` is off in production; CORS is an allowlist

- **Where:** `make_app` in kernel/http.py; `ALLOWED_ORIGINS`
- **Why:** OpenAPI docs are a development aid and an information leak in production. The browser
  normally calls same-origin through the rewrite, so CORS is a backstop.

### BE-35 · Project id comes from `GCLOUD_PROJECT` as an alias

- **Where:** [kernel/config.py](../../backend/functions/kernel/config.py)
- **Why:** a deployed function's dotenv can't set `FIREBASE_*` (reserved prefix); the CLI sets
  `GCLOUD_PROJECT` at discovery and runtime. Domain settings (buckets, mail) live in each
  subdomain's own `settings.py`, so the kernel knows no domain.

### BE-36 · One region, one runtime identity, three instances by default

- **Where:** `set_global_options` in main.py; `DEFAULT_REGION` in kernel/http.py
- **Decision:** `asia-south1` (Mumbai, next to Firestore), every function as `functions-runtime@`,
  `max_instances=3` (media processing: 2, 1 GiB).
- **Why:** latency to the owner and the database; least privilege; a cost ceiling on a personal site.

### BE-37 · Two Python environments

- **Where:** Makefile `setup-backend`
- **Decision:** uv's `.venv/` for lint/test, plus a stdlib `venv/` and an exported `requirements.txt`.
- **Why:** the Firebase CLI can't detect the runtime or load any function without the latter.

### BE-38 · Logs are single-line JSON

- **Where:** [kernel/logging.py](../../backend/functions/kernel/logging.py)
- **Why:** Cloud Logging parses JSON lines into queryable fields (`severity`, extra fields); the
  monitoring module's error metric relies on it.

## Data access (ADR 0022)

### BE-39 · The media library answers "where is this image used?", and delete enforces it

- **Where:** `find_references` in [media/library/repository.py](../../backend/functions/src/media/library/repository.py), `LibraryService.usage` / `.delete`
- **Decision:** `GET /{id}/usage` lists `collection/id` of every content document — drafts
  included — that mentions the asset's URL or thumbnail URL. `DELETE` raises 409 while that list
  is non-empty, unless `?force=true` (sent only after the admin has seen the list and confirmed).
  The content collections are scanned by name (`CONTENT_COLLECTIONS`), not by importing the
  content domain; a registry test keeps that list equal to the schemas' `publicRead` collections.
- **Why:** the check used to live in a Next.js route, so the API's delete didn't enforce it — any
  caller but the admin UI could delete an image a live page still showed. And ADR 0022 moves every
  read into the API.
- **Outcome:** the rule holds for every caller. Cost: a full scan of the content collections per
  check — fine at tens of documents.
- **Related:** ADR 0022 · ADR 0017 · supersedes BE-30
- **Since:** 2026-10-20

### BE-40 · Public reads live in `CrudService`, beside the admin routes

- **Where:** `list_public`, `get_public`, `to_public`, `reachable_by_url` in [kernel/crud/service.py](../../backend/functions/kernel/crud/service.py); `GET /public` in each content subdomain's `routes.py`; `ProjectService`
- **Decision:** each content subdomain serves an unauthenticated `GET /public` (projects also
  `GET /public/{slug}`) from the same function as its admin routes. `list_public` returns only
  `public` documents in `order`; `get_public` 404s unless the visibility is in
  `reachable_by_url` (projects add `unlisted`). `to_public` drops `audit` (it names the admin's
  uid), and `ProjectService.to_public` strips a confidential client's name and logo. Responses
  omit nulls. Projects reserve the slugs `public` and `reorder` so a project can't shadow a route.
- **Why:** the visibility and confidentiality rules must apply to every public read, so they sit
  in the one service every read passes through — not in each route, and not in the frontend.
  Serving them from the existing functions adds no deploys and no extra cold starts.
- **Outcome:** the frontend gets exactly what a visitor may see. Cost: the routes are public; they
  serve only what the pages already show, and `max_instances` caps abuse.
- **Related:** ADR 0022 · FE-26
- **Since:** 2026-10-20
