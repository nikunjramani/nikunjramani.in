# 0011 · Domain-wise separate Firebase Functions

**Status:** ✅ Accepted · **Date:** 2026-09-06
**Supersedes:** [0003 · FastAPI inside a single HTTP function](./0003-fastapi-in-a-single-function.md)

---

## Context

[ADR 0003](./0003-fastapi-in-a-single-function.md) put the entire API in one deployed function, on
the grounds that shared routing and middleware were worth more than isolation.

In review that was judged the wrong trade. One function holding every route means:

- All code — every router, service and repository — loads on **every** cold start, whichever
  endpoint was called
- A bad deploy takes down the whole API, including the public contact form
- Contact-form traffic and admin CRUD share one set of instance limits despite having nothing in
  common
- The folder structure is organised by technical layer rather than by what the code is *about*,
  so the code for one feature is scattered across four directories

The preference stated was explicit: separate functions, grouped by domain, with everything about a
domain living together — `functions/src/contact/` holding all contact-related code.

## Decision

**One deployed function per domain**, with each domain owning its handlers, service, repository,
triggers and tests in a single directory.

```
backend/functions/
├── main.py                 # imports and re-exports every function — the only entrypoint
├── shared/                 # imported by every domain, owns nothing itself
│   ├── core/               # config · firebase · security · errors · logging · rate_limit
│   ├── api.py              # make_function(): the FastAPI + a2wsgi wrapper, once
│   ├── repositories/base.py
│   └── generated/models/   # from architecture/schemas
└── src/
    ├── contact/            # ← everything contact, together
    │   ├── routes.py       # FastAPI router
    │   ├── service.py      # business rules
    │   ├── repository.py   # Firestore access
    │   ├── triggers.py     # on_contact_created → email
    │   └── tests/
    ├── projects/           # routes · service · repository · triggers · tests
    ├── skills/  experience/  education/  certifications/  posts/  profile/
    ├── media/              # + on_media_uploaded
    ├── messages/
    ├── settings/
    └── system/             # health · resume · sitemap · nightly_backup
```

Each domain exports one function through a shared three-line wrapper:

```python
# src/projects/__init__.py
from shared.api import make_function
from .routes import router

api_projects = make_function(router, name="api_projects")
```

**FastAPI is retained**, per domain rather than globally. Pydantic validation and generated
OpenAPI were the reason for choosing it in 0003, and neither depends on there being only one
function.

**Rewrites keep the API surface unified**, so the frontend still sees one base URL
(see the implementation note at the end — the mechanism is Next.js, not Firebase Hosting):

```jsonc
"rewrites": [
  { "source": "/api/v1/projects/**", "function": "api_projects" },
  { "source": "/api/v1/contact/**",  "function": "api_contact"  }
]
```

## Consequences

### What this makes easier

- **Cold starts get smaller.** A function imports only its own domain plus `shared/`, instead of
  the entire API surface
- **Blast radius is contained.** A broken projects deploy leaves the contact form running
- **Deploys are independent and fast** — `firebase deploy --only functions:api_projects`
- **Per-domain instance limits and memory**, tuned to actual need rather than to the worst case
- **The code for one feature lives in one directory.** Adding a field touches
  `src/projects/` and nothing else
- Per-domain metrics and logs in Cloud Logging, without filtering
- Domain boundaries become explicit — a cross-domain import is visible in review

### What this makes harder — the cost we're accepting

- **Roughly 14 deploy units instead of 1.** Managed by Terraform and a single `make deploy`, but
  it's more moving parts to reason about
- **The admin panel warms several functions.** A session that touches projects, then media, then
  messages pays three separate cold starts rather than one. This is the real cost — a few seconds
  of first-use latency per screen, for a single user. Judged acceptable; a `min_instances` bump on
  the busiest domain is available if it grates
- **OpenAPI docs fragment** across functions — one spec per domain rather than one for the API
- **Rewrites become load-bearing.** Adding a domain means adding a rewrite, and forgetting
  produces a 404 that looks like a routing bug
- Shared code needs real discipline. `shared/` may never import from `src/`

### Guardrails

- `shared/` importing from any `src/` domain is a circular dependency and is banned — enforced in
  review and by an import-linter rule
- One domain importing another's `repository` or `service` is banned. Cross-domain work goes
  through an event or through `shared/`
- Every domain directory has the same shape, so a new one is copy, rename, register

## Alternatives considered

### One function for everything (ADR 0003)
Superseded. Simplest deployment, but couples every domain's availability, cold start and scaling to
every other domain's.

### One function per endpoint
Maximum isolation. Rejected: ~30 deploy units, and routing plus shared middleware would have to be
rebuilt by hand for each.

### Domain-wise folders, single deployed function
Would give the code organisation without the deploy fragmentation, and was tempting. Rejected
because it keeps every drawback of 0003 — shared cold start, shared blast radius, shared limits —
while only fixing the cosmetic complaint.

## Revisit if

- Cold starts across multiple domains make the admin panel genuinely unpleasant to use
- Deploy time for ~14 functions becomes a bottleneck
- Two domains turn out to be so coupled that splitting them was artificial

---

## Implementation note — added 2026-09-06, during Phase 0

**The unification mechanism above is wrong.** Firebase **App Hosting does not support
`firebase.json` rewrites** — that is classic Firebase Hosting, a separate product. App
Hosting serves the framework backend through a load balancer and offers no rewrite config;
routing to Functions has to happen inside the application.

The decision itself is unaffected: one function per domain still stands, and the API
surface is still unified. The mechanism is **Next.js rewrites** in `next.config.ts`:

```ts
async rewrites() {
  return DOMAINS.map((domain) => ({
    source: `/api/v1/${domain}/:path*`,
    destination: `${FUNCTIONS_BASE}/api_${domain}/:path*`,
  }));
}
```

This turns out to be better than the original plan. The browser only ever talks to one
origin, so there is **no CORS preflight on any API call** and cookies need no special
handling. The cost is one extra hop through the already-warm Next server — acceptable on a
write-only path used by one admin and the occasional contact form.

If that hop ever matters, the escape hatch is calling the per-domain function URLs
directly, with CORS configured — which `shared/api.py` already does.

*Recorded as an implementation note rather than a new ADR: the decision did not change,
only a factual assumption about how the platform works.*

---

## Implementation note — added 2026-09-12, during Phase 3

**Cold-start isolation, the headline benefit of this ADR, was not actually happening** with the
obvious implementation — `main.py` doing a flat `from src.X import api_X` for every domain.

`functions_framework` (the runtime `firebase-functions` builds on) loads a function by fully
executing `main.py` and then plucking the one requested function out of the resulting module —
confirmed by reading `functions_framework._function_registry` directly, and separately in
`firebase_functions.private.serving.get_functions`, which does the same for `firebase deploy`'s own
manifest discovery. A flat import list means every cold start — regardless of which single domain
is actually about to serve the request — imports and fully constructs the FastAPI app for every
*other* domain too. That is exactly as expensive as the single-function design this ADR replaced,
just now duplicated across ~14 separate containers instead of paid once.

The fix, in `main.py`: import conditionally on the `FUNCTION_TARGET` environment variable.

```python
_target = os.environ.get("FUNCTION_TARGET")

def _wanted(name: str) -> bool:
    return _target is None or _target == name

if _wanted("api_contact"):
    from src.contact import api_contact
```

`FUNCTION_TARGET` is unset wherever every function needs to be visible at once — the emulator, the
test suite, and the CLI's manifest-discovery pass — so those get the same "import everything"
behaviour as before, unchanged. It is set to exactly one function's name inside that function's own
deployed container, where the conditional actually does its job.

**This is now a fifth thing "adding a domain" requires**, alongside the schema, the router wiring,
the `next.config.ts` rewrite and the import-linter contract entry: a new `if _wanted(...):` line in
`main.py`. Forgetting it does not break anything visibly — the domain still works when invoked
directly during discovery/testing — it just quietly loses the isolation this ADR exists for. See
the `add-api-endpoint` skill and [CLAUDE.md](../../CLAUDE.md) for the checklist.

