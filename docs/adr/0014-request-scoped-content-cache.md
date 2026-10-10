# 0014 · Render mutable content per request

**Status:** Accepted · **Date:** 2026-10-10

## Context

A production smoke test requested a draft project's URL (404), published it, and
continued receiving the CDN's cached 404. Its response advertised `s-maxage=3600`.
Calling Next.js tag revalidation did not invalidate that App Hosting CDN response.
Instance-local data caches also cannot guarantee coherent invalidation across three
Cloud Run instances. This violates the requirement that admin edits appear promptly
and can retain content after it is made private.

## Decision

Public content pages, sitemap and project Open Graph images render per request.
Firestore reads use React `cache` for deduplication within a render, replacing the
one-hour persistent `unstable_cache`. The authenticated revalidation webhook remains
compatible with backend writes and expires any tagged cache immediately.

This supersedes ADR 0005's ISR/CDN caching consequence, not its read/write boundary:
Next.js still reads Firestore directly, and Python owns writes. Static assets retain
normal immutable CDN caching.

## Consequences

New requests see current publication state without waiting for CDN expiry or relying
on which instance receives the webhook. Firestore reads and SSR invocations increase;
scale-to-zero means frontend cold starts remain possible. Monitor cost and latency.
Already-open browser pages still require navigation or refresh to see edits.

Reintroduce persistent content caching only with a demonstrated shared cache and CDN
purge mechanism, including publish-after-404 and public-to-private regression checks.

## References

- https://firebase.google.com/docs/app-hosting/optimize-cache
- Installed Next.js documentation: caching without Cache Components; revalidateTag
