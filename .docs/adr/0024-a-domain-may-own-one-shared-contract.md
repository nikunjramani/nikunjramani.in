# 0024 · Let a domain own one shared contract module its subdomains import

**Status:** ✅ Accepted. Amends the "no shared code within a domain" part of [0017](./0017-bounded-context-domains.md); the rest of 0017 stands.
**Date:** 2026-10-21
**Deciders:** Nikunj Ramani

---

## Context

ADR 0017 split the backend into domains of self-contained subdomains. To stop a domain's
`common/` folder from swallowing its subdomains again, it went further: subdomains share nothing
inside their domain. When two of them need the same convention, each spells out the part it uses
and a test holds the copies to one contract.

Each subdomain was then its own Cloud Function, so that duplication also bought independent
deploys. Since ADR 0023 the whole backend is one Cloud Run service. The copies no longer buy
anything at deploy time.

The media domain shows the cost most clearly. Upload, processing and library all work on one
bucket:

- `MediaSettings` (the bucket's name) was defined three times.
- `processed_path` and `thumbnail_path` appeared twice.
- The upload path's shape was written once and re-parsed twice.
- `tests/media/test_layout.py` existed only to prove these copies agreed.

A change to the bucket layout meant editing three subdomains and trusting the test.

## Decision

A domain may have **one module at its root that its subdomains import**, holding a **contract**
they all must agree on, and nothing else. For media that module is `src/media/bucket.py`. It holds:

- the bucket's name (`MediaSettings`)
- its layout (`UPLOAD_PATTERN`, `new_upload_path`, `asset_id_of`, `processed_path`,
  `thumbnail_path`, `public_url`)
- the shared Storage client

The rules that keep it from becoming `common/` again:

- **It holds a contract, never a job.** No service, no repository, no route, no business rule.
  What a subdomain *does* with the bucket stays in that subdomain (`*/storage.py`).
- **One module per domain**, named for what it describes (`bucket.py`), never `common`, `shared`
  or `utils`.
- **Only that domain's subdomains import it.** The import-linter independence contracts already
  stop other domains, and sibling subdomains still never import each other.
- **It needs a reason the code can show:** something that must be identical across subdomains,
  where a disagreement is a bug.

## Consequences

### What this makes easier

- A change to the bucket's layout is one edit, and type-checking finds every caller.
- The test that only checked three copies agreed becomes a test of the contract itself
  (`tests/media/test_bucket.py`).
- One Storage client per process instead of a new one per request.

### What this makes harder — the cost we're accepting

- A subdomain is no longer fully readable on its own. To understand media/upload, you also read
  `src/media/bucket.py`.
- The line between "contract" and "job" is a judgement call that review has to hold. The failure
  mode this ADR risks is the one 0017 was written against: a root module that slowly gains logic.

## Alternatives considered

### Keep the copies (0017 as written)
This made sense while each copy deployed separately. Inside one service it's duplication with a
test attached, and nothing is gained in return.

### Put the bucket layout in `kernel/`
`kernel/` is domain-free infrastructure. It must not know that media exists or how its bucket
is laid out.

### Do the same for inbox now
Inbox's subdomains share the `contact_messages` collection, but each repository does different
work over it (store a message, triage messages). No constant or shape is duplicated, so there's
no contract to extract yet.

## Revisit if

- A domain's root module grows something that isn't a contract (a function with a rule in it,
  a Firestore call). Move that back into a subdomain.
- A second domain wants one. Check that it meets the same test before adding it.
