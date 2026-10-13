# 0015 · Remove the cache-revalidation webhook

**Status:** ✅ Accepted — supersedes the webhook clause of [0014](./0014-request-scoped-content-cache.md)
**Date:** 2026-10-13
**Deciders:** Nikunj Ramani

---

## Context

Before ADR 0014, public pages were cached with tagged `unstable_cache`, and every admin write
told the site to drop those tags: `ContentService` called `shared/services/revalidate.py`, which
POSTed the collection name to `/api/revalidate`, authenticated with a `REVALIDATE_TOKEN` secret
shared between the functions and App Hosting.

ADR 0014 removed persistent content caching — pages now render per request — but kept the
webhook "for compatibility". Nothing reads a tag any more, so the webhook invalidates nothing.
It still costs something on every write: an outbound HTTP call (3 s timeout) inside the admin
request, a secret bound to eight functions and to App Hosting, and an App Hosting identity that
can read every secret in the project because it needed this one.

## Decision

Remove the whole chain: `shared/services/revalidate.py`, `ContentService`'s `bust_cache`, the
`/api/revalidate` route, the `REVALIDATE_TOKEN` / `REVALIDATE_URL` settings and the
`REVALIDATE_TOKEN` secret. App Hosting reads no secrets, so its service account loses
`secretAccessor` on all of them.

## Consequences

### What this makes easier

- Admin writes no longer wait on a call to the frontend.
- App Hosting holds no secret at all; secret access is functions-only.
- One fewer secret to rotate across two deploy targets.

### What this makes harder — the cost we're accepting

- Reintroducing a persistent cache (ADR 0014's "revisit if") now means rebuilding an
  invalidation path too — but 0014 already requires a new design for that (a shared cache and a
  CDN purge), which this webhook was never going to be.
- `terraform apply` destroys the `REVALIDATE_TOKEN` secret. Deploy App Hosting with the updated
  `apphosting.yaml` first, so no rollout still references it.

## Alternatives considered

### Keep it dormant
"Compatible" code with no reader is the kind of thing a stranger reasonably assumes works.
Its only effect was cost and secret sprawl.

## Revisit if

- Persistent content caching comes back with a real CDN purge — design the invalidation then.
