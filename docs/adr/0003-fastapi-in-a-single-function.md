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
