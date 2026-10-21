# 0017 · Organise the backend as isolated domains of self-contained subdomains

**Status:** ✅ Accepted — deployment (one function per subdomain) superseded by [0023](./0023-backend-as-one-cloud-run-service.md). Supersedes the code-structure parts of [0011](./0011-domain-wise-separate-functions.md), [0012](./0012-generic-content-crud-in-shared.md) and [0016](./0016-content-domains-from-a-factory.md).
**Date:** 2026-10-13
**Deciders:** Nikunj Ramani

---

## Context

ADR 0011 split the backend into twelve flat domains under `src/`, one Cloud Function each.
Every domain still leaned on a large `shared/` package that held real business code: the
generic CRUD service and router, the repositories, the audit, email, image and storage
services, the rate limiter and the collection list. import-linter showed the domains as
independent only because they all went through `shared/`. In practice they were coupled:

- `contact` and `messages` were two domains over one collection.
- `media` scanned every content collection to count image usage.
- `system` read the audit trail every other domain wrote.

A change to `shared/` was a change to all twelve domains at once. A first restructure
grouped the domains but moved the sharing into a `common/` folder per domain, which left a
subdomain as a thin `main.py` over shared code. That defeated the point and was dropped.

## Decision

- **Main domains** (`content`, `media`, `inbox`, `ops`, `identity`) live in
  `src/<domain>/`. They never import each other, and they meet only through Firestore
  documents whose shape `architecture/schemas` defines.
- **Subdomains** live in `src/<domain>/<sub>/`. Each does one job and deploys as its own Cloud
  Function, `api_<domain>_<sub>`, served at `/api/v1/<domain>/<sub>`. Each owns every file for
  its job: `main.py` (the Firebase function), `routes.py`, `schemas.py`, `service.py`,
  `repository.py`, plus any settings, storage or paths modules it needs.
- **There is no `common/` folder.** Subdomains don't import siblings. When two subdomains need
  the same convention, each owns the part it uses, and a test holds the copies to one contract
  (for example `tests/media/test_layout.py`).
- **Entry points come in three levels:**
  - each subdomain's `main.py` defines its function
  - each domain's `main.py` lists its functions by name, without importing them
  - the root `main.py` merges those lists and imports only the module `FUNCTION_TARGET` names
- **`kernel/` holds only infrastructure that is identical for every subdomain and has no
  domain rule in it:** the HTTP adapter, auth, the audit writer and the model-agnostic CRUD
  base (`kernel/crud`). A content subdomain's repository and service subclass that base; its
  routes are written out in full.
- **Generated models stay in one package, `shared/generated`.** `shared/` holds nothing else
  and imports nothing of ours, so it can ship as its own package.
- **API route names live in `architecture/api-routes.json`.** Code generation produces the
  typed frontend contract and Next.js consumes that generated registry for its rewrites;
  registry tests keep it aligned with deployed function names and Terraform.
- **Cross-domain reads move to Next.js**, consistent with ADR 0005. The media "where is this
  image used?" check is the example.
- **A new `identity` domain** lists, grants and revokes the `admin` custom claim. Sign-in
  stays Google in the browser.
- **All tests live in `tests/`**, mirroring `src/` and `kernel/`.
- **There are no `__init__.py` files** outside `shared/generated`. The code uses implicit
  namespace packages, pytest runs in `importlib` mode, and mypy uses
  `explicit_package_bases`.

Import-linter enforces the import rules. `tests/test_import_rules.py` enforces the layout
(no Firestore in routes or services, no `__init__.py`, no tests in `src/`, no `common/`).
`tests/test_domain_registry.py` enforces the hand-maintained registrations.

## Consequences

### What this makes easier

- **Each subdomain folder answers "where does X live?" for its job.** Every file in it serves
  that one job.
- **Editing a subdomain redeploys one function,** and nothing outside its domain can break.
- **A subdomain can be deleted or rewritten** without auditing its siblings.

### What this makes harder — the cost we're accepting

- **15 HTTP functions instead of 12,** which means more cold starts and more instance caps to
  watch.
- **Deliberate duplication:**
  - media's bucket-layout helpers appear three times, held together by a test
  - media and inbox have purpose-built repositories per subdomain over one collection
  - each subdomain has its own settings module
- **Every function name and admin URL changes once.** That needs a one-time deploy migration
  (`.docs/RUNBOOK.md`).
- **Changes to `kernel/` or `shared/` redeploy everything,** so both must stay small.

## Alternatives considered

### A `common/` folder per domain
This was tried first. Subdomains became thin wrappers around shared code, so the boundary
existed only on paper.

### Strictly nothing shared, kernel included
Each subdomain would carry its own copy of the WSGI bridge, auth and CRUD rules. The a2wsgi
fork hang shows the risk: one infrastructure fix would have to be repeated in eighteen
places.

### Each content subdomain carries a full copy of the CRUD rules
That would be about 150 lines eight times over, and a fix to the publish rules would need
eight edits.

### One function per main domain
Fewer cold starts, but subdomains would lose their own deploy, blast radius and instance
limits.

### Models generated per domain
Rejected in favour of one generated package, planned to be released for other consumers.

## Revisit if

- **Cold starts across 15 functions become visible on admin screens.** Content subdomains
  could then share one function without changing the code layout.
- **Two subdomains keep needing the same logic beyond a small convention.** That is a sign
  the boundary is in the wrong place.
