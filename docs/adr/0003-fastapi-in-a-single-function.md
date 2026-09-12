# 0003 · FastAPI inside a single HTTP function

**Status:** 🔄 Superseded by [0011](./0011-domain-wise-separate-functions.md) · **Date:** 2026-09-06

> Superseded on 2026-09-06. The FastAPI-and-`a2wsgi` choice below still stands; what changed is
> that it now applies **per domain** rather than to one global function. See
> [ADR 0011](./0011-domain-wise-separate-functions.md).

---

## Context

The Firebase Functions Python SDK exposes HTTP handlers as `on_request`, which hands the handler a
`flask.Request`. FastAPI is ASGI, so it doesn't drop into that signature directly.

There are roughly thirteen admin CRUD resources plus several public endpoints — enough that routing,
shared middleware and consistent validation matter.

## Decision

Run **one FastAPI application inside a single `api` HTTP function**, adapted with `a2wsgi`.
Firestore, Storage and scheduled triggers stay as separate discrete functions, since they're
genuinely separate entrypoints.

## Consequences

### What this makes easier

- Pydantic validation on every request, using the models generated in
  [0006](./0006-json-schema-source-of-truth.md)
- OpenAPI docs generated automatically — the admin panel can be built against a real spec
- Shared dependencies (auth, rate limiting, pagination) written once
- Standard router/service/repository layering
- **Portable.** The app is a normal FastAPI app; the Firebase adapter is a handful of lines

### What this makes harder — the cost we're accepting

- One extra dependency and one indirection layer to understand when debugging
- ASGI→WSGI bridging means no streaming responses or WebSockets — neither is needed here
- All API routes share one function's cold start and one set of instance limits

## Alternatives considered

### Plain Flask
Native fit, zero adapter. Rejected: loses Pydantic validation and OpenAPI generation, which are
precisely what makes the generated models pay off. We'd hand-write validation instead.

### One function per endpoint
Best cold-start isolation and independently scalable. Rejected: no shared routing or middleware,
~18 deploy units for a personal site, and a bigger deploy surface than the problem justifies.

## Revisit if

- Cold starts on the API become user-visible
- A single endpoint develops resource needs wildly different from the rest

---

## Implementation note — added 2026-09-12, during Phase 3

**`a2wsgi.ASGIMiddleware` is not used directly, even though the FastAPI-via-`a2wsgi` decision
above still stands.** Firebase's own deploy tooling forced this: it requires a `requirements.txt`
at the function source root and a stdlib `venv/` it manages itself (distinct from the `uv`-managed
`.venv/` used for local dev, lint and test), or `firebase deploy`/`firebase emulators:start` cannot
detect the runtime or load the function at all. Neither is optional — `make setup-backend` now
generates both.

With that in place, a real end-to-end request through the emulator — the exact test this ADR's
own Alternatives section assumed would already work — hung indefinitely. `os.fork()` reproduced it
directly: `ASGIMiddleware` starts a persistent background thread running its own event loop at
*construction* time, and `os.fork()` only duplicates the calling thread. Werkzeug's dev-server
reloader (which `functions-framework` uses locally) forks, so the child inherits a dead copy of
that thread — Python even warns about this at the fork call
(`this process is multi-threaded, use of fork() may lead to deadlocks in the child`). Every
subsequent request then hangs forever, waiting via
`asyncio.run_coroutine_threadsafe(coro, self.loop).result()` on a loop nothing will ever run again.

Direct in-process calls (`Response.from_app` from a synthetic Flask test context, even from a
background thread) all worked fine — the corruption only shows up once an actual fork happens,
which is exactly the gap between unit-testing the adapter and running it through the real
emulator. This is the reason [Phase 3](../plan/phases/phase-3-backend.md) explicitly calls for
verifying `make_function()` against the emulator itself before building further domains on it,
rather than trusting a `TestClient` call.

The fix, in `shared/wsgi_bridge.py`: reuse a2wsgi's `build_scope` (a small, pure,
stateless WSGI-environ-to-ASGI-scope converter with no threading of its own) but drop
`ASGIMiddleware`/`ASGIResponder` entirely, replacing them with a bridge that runs each request via
a fresh `asyncio.run()` — no persistent thread, so nothing can be left dangling by a fork. This is
strictly less efficient per call than a warm, reused event loop, which does not matter here: a
Cloud Function cold-starts fresh per instance and handles one request at a time regardless.

Verified against the real emulator, not just `TestClient`: a POST to `/contact` through the
deployed `api_contact` function persisted correctly to Firestore, a honeypot-tripped submission
returned the identical response without creating a document, and a missing-field submission
produced a real 422 — all instantly, with no hang. Confirmed separately that the same
`ASGIMiddleware` construction still hangs under a direct `os.fork()` test, isolating the fix to
exactly the mechanism described above.
