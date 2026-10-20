# 0022 · The Python API owns every read and write; the frontend never touches Firestore

**Status:** ✅ Accepted
**Date:** 2026-10-20
**Deciders:** owner

---

## Context

[ADR 0005](./0005-reads-bypass-python.md) split data access by direction: Python owned every
write, and Next.js Server Components read Firestore directly with the Admin SDK, so a page never
waited on a Python cold start (1–3 s after an idle period).

In practice that put database knowledge in two languages and two deployables:

- `frontend/src/lib/data/` knew collection names, the `visibility`/`order` query, the
  Timestamp conversion and the confidential-client rule — all of which the backend also knew.
- A cross-collection admin read (which content still uses a media asset) lived in a Next.js route
  handler, so the rule it protects was enforced only in the UI: the API's delete endpoint didn't
  check it.
- Changing the database — a collection name, a field's storage shape, or Firestore itself — meant
  changing and deploying both the backend and the frontend in step.

The owner asked for one place that touches the database, accepting slower page loads.

## Decision

**The Python API is the only code that reads or writes Firestore.** The frontend has no Firestore
SDK at all.

- Each content subdomain serves unauthenticated `GET /public` (and `GET /public/{id}` for
  projects) beside its admin routes. `CrudService.list_public`/`get_public` apply visibility
  (`unlisted` reachable by URL, never listed; drafts 404), drop the server-owned `audit` block,
  and — for projects — strip a confidential client's name and logo.
- Server Components read through `frontend/src/lib/data/`, which now calls those routes
  (`lib/data/api.ts`), server-to-server, straight to the function URL.
- "Where is this media asset used?" moved into `media/library` (`GET /{id}/usage`), and
  `DELETE` refuses an asset still in use unless `force=true` — the admin's confirmation.
- The App Hosting runtime identity loses `roles/datastore.viewer`; ESLint forbids importing any
  Firestore SDK in the frontend. The Admin SDK stays in the frontend only for Firebase Auth
  (minting and verifying the admin session cookie).

This supersedes ADR 0005.

## Consequences

### What this makes easier

- One place knows the database: a collection rename, a storage change or a different database is
  a backend change only; the frontend sees the same JSON.
- Rules that protect data live where the data is: visibility, confidential clients and "still in
  use" are enforced by the API for every caller, not by whichever UI happens to call.
- The frontend's server identity can't read the database at all, so a frontend bug can't leak a
  draft or a contact message.

### What this makes harder — the cost we're accepting

- **Page loads can wait on a cold start.** A visit after an idle period waits for the content
  functions to start (1–3 s, in parallel across the ones a page needs). The owner accepted this.
  If it becomes a problem, `minInstances: 1` on the read-heavy functions removes it for a small
  monthly cost.
- One more network hop per read (Next.js → Cloud Functions → Firestore) and more function
  invocations, which count against the free tier.
- The public routes are reachable by anyone. They serve only what the pages already show, and
  each function's `max_instances` caps the cost of abuse.

## Alternatives considered

### Keep ADR 0005, move only the media-usage check
Fixes the unenforced delete but leaves database knowledge in both codebases — the actual problem.

### A single "site" read function serving whole pages
One cold start per page instead of several in parallel, but it would read every content
collection from outside the content domain (ADR 0017), and duplicate each subdomain's rules.

### Keep a warm instance on every content function now
Removes the latency, but costs money for a problem not yet measured. Available later, unchanged.

## Revisit if

- Measured page latency from cold starts becomes a real complaint — add `minInstances` first.
- The function count or invocation cost becomes material.
