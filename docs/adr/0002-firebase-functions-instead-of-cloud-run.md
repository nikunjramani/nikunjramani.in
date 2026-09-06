# 0002 · Firebase Functions instead of standalone Cloud Run

**Status:** ✅ Accepted · **Date:** 2026-09-06

---

## Context

The backend was originally planned as a FastAPI container on Cloud Run. Firebase Functions was
requested instead.

Worth stating clearly, because it makes the decision cheap: **2nd-generation Cloud Functions for
Firebase run on Cloud Run.** This is not a choice between two platforms — it's a choice between two
toolchains over the same infrastructure.

## Decision

Deploy the backend as **2nd-generation Cloud Functions for Firebase**, managed through the Firebase
CLI alongside rules, indexes and hosting.

## Consequences

### What this makes easier

- One toolchain: `firebase deploy` covers functions, rules, indexes and hosting
- One project and one billing view for everything
- Firestore and Storage **triggers come free** — event-driven work (email on contact, image
  processing on upload, cache busting on publish) needs no extra plumbing
- Scheduled functions without provisioning Cloud Scheduler separately
- Secret Manager integration is declarative

### What this makes harder — the cost we're accepting

- Slightly less control over the container image than a hand-written Dockerfile
- The Firebase abstraction occasionally hides Cloud Run detail you need when debugging
- Runtime versions are gated on Firebase adopting them, not on Cloud Run supporting them

Because the API is a plain FastAPI app behind a thin adapter
([0003](./0003-fastapi-in-a-single-function.md)), moving to standalone Cloud Run later is a
configuration change, not a rewrite. That portability is what makes this reversible.

## Alternatives considered

### Standalone Cloud Run
More container control, but a second toolchain, a second deploy pipeline, and no native Firestore
triggers. Nothing gained for this workload.

### Firestore-only, no backend at all
Would mean client-side writes, which [0007](./0007-deny-all-client-writes.md) rules out, and no
server-side place for secrets or spam filtering.

## Revisit if

- Cold starts become a problem on a path where they're user-visible
- We need a runtime or a system dependency Firebase Functions won't support
