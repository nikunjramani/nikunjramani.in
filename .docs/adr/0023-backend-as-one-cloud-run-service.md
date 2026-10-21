# 0023 · Run the backend as one FastAPI service on Cloud Run, keeping its domains and subdomains

**Status:** ✅ Accepted
**Date:** 2026-10-21
**Deciders:** owner

---

## Context

The backend is FastAPI, but it ships as **18 Cloud Functions for Firebase** (2nd gen): one HTTP
function per subdomain (`api_<domain>_<sub>`, 15 of them, [ADR 0011](./0011-domain-wise-separate-functions.md),
[ADR 0017](./0017-bounded-context-domains.md)) plus three event functions — `on_media_uploaded`
(Storage), `on_contact_created` (Firestore) and `nightly_backup` (schedule).

A 2nd-gen function already *is* a Cloud Run service with an Eventarc or Cloud Scheduler trigger in
front of it; the Firebase Functions SDK generates those for us. What that layer costs:

- **Cold starts multiply.** Each subdomain starts on its own; since [ADR 0022](./0022-backend-owns-all-data-access.md)
  the home page calls four content functions, so a quiet-period visit can wait on four starts.
- **One request at a time.** Deployed at 256 MiB, each function gets 0.17 vCPU and concurrency 1,
  capped at 3 instances.
- **Glue code with its own failure modes.** FastAPI is wrapped into a Flask handler through
  `kernel/http.py` and a hand-written WSGI bridge (`kernel/wsgi_bridge.py`), because a2wsgi's thread
  hangs after the Functions runtime forks. Root `main.py` imports by `FUNCTION_TARGET`.
- **Four registrations per subdomain** — the domain's `FUNCTIONS` table, `api-routes.json`, the
  import-linter contracts and Terraform's `http_functions` — each silent in production if missed.
- **Two Python environments** (uv's `.venv/` plus the stdlib `venv/` + `requirements.txt` the
  Firebase CLI needs), a functions emulator with no working debugger, and a `firebase deploy` that
  rebuilds all 18 on any `kernel/` change.

What the 15 deployments *don't* buy is isolation in the code: that comes from the domain/subdomain
layout and import-linter, which hold regardless of how the code is deployed.

The owner asked to keep Firestore for now (a move to PostgreSQL may follow as its own decision)
and to keep the domain/subdomain structure.

## Decision

**The backend runs as one FastAPI application, deployed as one Cloud Run service named `api`,
from one container image.** Firestore, Firebase Auth, App Check and Cloud Storage stay.

- **Code structure is kept.** `src/<domain>/<subdomain>/` keeps `routes.py` · `schemas.py` ·
  `service.py` · `repository.py`; domains never import each other, subdomains never import
  siblings, enforced by the same import-linter contracts. A subdomain's `main.py` (it existed only
  to deploy a function) is removed. A subdomain that reacts to an event gains `events.py`, an
  `APIRouter` like `routes.py`.
- **`apps/api.py` assembles the app**: it mounts each subdomain's router at
  `/api/v1/<domain>/<sub>` and each `events.py` router under `/internal/…`. That file plus
  `architecture/api-routes.json` are the only registrations; a test fails if a subdomain is missing
  from either.
- **Events and jobs are HTTP routes on the same service.** Eventarc delivers the Storage
  `object.finalized` and Firestore `document.created` events, and Cloud Scheduler calls the backup
  job, each with a Google-signed OIDC token for the service's runtime account (`functions-runtime@`,
  which the service already runs as). `/internal/*` routes accept only that token (issuer,
  audience = one of the service's URLs, email = that account), verified in `kernel/` the way
  `AdminClaims` verifies admins.
- **The service is public at the Cloud Run layer**, as the functions are today; admin routes
  authenticate in-process (`AdminClaims`), the contact route with App Check, `/internal/*` with
  the OIDC check above.
- **Sizing:** 1 vCPU, 1 GiB, concurrency 80, min 0 / max 3 instances, `asia-south1` (beside
  Firestore). 1 GiB covers image processing, which is rare and admin-only.
- **CI owns the service; Terraform owns what points at it.** CI builds the image, pushes it to
  Artifact Registry and deploys it with one Makefile target (`make deploy-api`), which carries the
  service's whole shape; runtime config moves from the Firebase CLI's `.env.<project>` files to
  `backend/deploy/<project>.yaml`. Terraform holds the Eventarc triggers and the scheduler job. The
  split is forced: staging's Terraform applies only from `main`, so a Terraform-created service
  couldn't exist for the pull request that introduces it — the preview has to create it, as
  `firebase deploy` created functions.

## Consequences

### What this makes easier

- One cold start serves every endpoint; one warm instance handles 80 requests at once. If cold
  starts ever matter, `min_instances = 1` is one setting for the whole API.
- Adding an endpoint is a route; adding a subdomain is a folder plus two lines.
- Plain local development: `uvicorn apps.api:app --reload`, a real debugger, one `/docs`.
- One deploy, one log stream, one place to roll back (Cloud Run keeps revisions).
- Deletes `kernel/http.py`, `kernel/wsgi_bridge.py`, root `main.py`, every `FUNCTIONS` table and
  subdomain `main.py`, the second venv, `requirements.txt`, the `firebase-functions` and `a2wsgi`
  dependencies, and the per-function Terraform and Next.js rewrite lists.

### What this makes harder — the cost we're accepting

- **Less runtime isolation.** A crash loop or a memory spike affects every endpoint, not one
  subdomain. Mitigated by tests, by Cloud Run keeping the previous revision for instant rollback,
  and by the processing work being small and rare.
- **Triggers become infrastructure we write.** Eventarc triggers, the Cloud Scheduler job and
  their IAM were generated by the Firebase SDK; now they're Terraform we own. Firestore events
  arrive as protobuf, so the contact trigger needs Google's event types (`google-events`, whose
  last release is 2024-12).
- **The runtime account keeps its old name** (`functions-runtime@`): service accounts can't be
  renamed, and a new one would mean re-granting every role for a label.
- **The `/internal/*` routes sit on a public service**, so their protection is our code, not
  Cloud Run IAM. One dependency, tested on its own like `require_admin`; misconfiguring it would
  expose the backup job and the event handlers.
- **Local events aren't automatic.** The Storage emulator can't deliver to Eventarc; in
  development an event is replayed by hand (documented in the RUNBOOK).
- A Dockerfile and an Artifact Registry repository to maintain (with an image cleanup policy).

## Alternatives considered

### Keep 15 + 3 Cloud Functions
Isolation the code already has, at the cost listed in Context. Rejected.

### Terraform owns the service too
The usual split, and the first plan. Rejected because staging's infra applies only from `main`
(ADR 0019), so the PR adding the service couldn't preview it; CI owning it mirrors how
`firebase deploy` owned the functions.

### Two services: a public `api` and a private `worker` for events and jobs
Cloud Run IAM would protect the event routes with no code, and image processing couldn't compete
with page reads. Rejected for now as more than this site needs: uploads are rare and admin-only,
and the OIDC check is a few tested lines. The same image can be deployed as a second service later
without code changes if uploads become heavy.

### One service per domain (5 services)
Keeps per-domain deploys, but reintroduces most of the cold-start and configuration cost for
isolation the import-linter contracts already provide.

### Rewrite on Django
Discarded in discussion on 2026-10-21: the routes, services, rules and tests carry over to a
FastAPI app as they are; Django would replace them and the JSON-Schema-generated models
([ADR 0006](./0006-json-schema-source-of-truth.md)), and its admin would duplicate the Next.js one.

## Revisit if

- Image processing (or a new heavy job) measurably slows requests → split a `worker` service
  from the same image.
- One domain needs a different scale, memory or release cadence → deploy that domain's routers
  as its own service from the same image.
- The move to PostgreSQL is decided → that is a repository-layer change under this structure,
  plus a new ADR.

Supersedes [ADR 0002](./0002-firebase-functions-instead-of-cloud-run.md) (Firebase Functions
over Cloud Run), [ADR 0011](./0011-domain-wise-separate-functions.md) (one function per domain) and
the "one subdomain = one deployed function" part of [ADR 0017](./0017-bounded-context-domains.md),
whose code structure stands.
