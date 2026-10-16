# 0005 · Reads bypass Python entirely

**Status:** ✅ Accepted · **Date:** 2026-09-06

---

## Context

There's a Python backend and a Firestore database. The obvious architecture routes everything
through the API: browser → Next.js → Python → Firestore.

That's also the architecture that makes free-tier personal sites feel slow. Python functions scale
to zero and cold-start in 1–3 seconds. On the read path that's 1–3 seconds of blank page on the
first visit after any quiet period — which, for a personal site, is most visits.

Keeping an instance warm costs money and defeats scale-to-zero.

## Decision

**Reads go straight from Next.js Server Components to Firestore** via the Firebase Admin SDK.
**Python owns every write.**

```
visitor → Next.js (SSR/ISR) → Firestore              ← reads, no Python
you     → /admin  → Python API → Firestore           ← writes
visitor → contact → Python API → Firestore           ← writes
```

## Consequences

### What this makes easier

- Page loads never wait on a cold start, ever
- Fewer moving parts on the path that matters most for user experience
- ISR caches rendered pages at the CDN, so most visits don't even hit Firestore
- Cold starts stay confined to writes, where a spinner makes them invisible
- Python's validation, business rules and secret handling apply to 100% of mutations

### What this makes harder — the cost we're accepting

- **Read logic lives in TypeScript, write logic in Python.** Two languages touching the same data.
  Mitigated by [0006](./0006-json-schema-source-of-truth.md) — both sides use models generated from
  the same schemas, so the shapes cannot drift.
- Query logic could get duplicated. Contained by keeping all reads in `frontend/src/lib/data/`.
- The frontend holds Admin SDK credentials server-side, so `import "server-only"` discipline is
  load-bearing.

## Alternatives considered

### Everything through Python
Single language for all data access. Rejected on cold starts — the user-visible cost is too high
for a benefit that's mostly aesthetic.

### Client-side Firestore SDK for reads
No server round trip at all. Rejected: content fetched client-side isn't in the server-rendered
HTML, which reintroduces exactly the SEO problem [0001](./0001-nextjs-instead-of-flutter-web.md)
was written to solve.

### Keep a warm instance
Costs money continuously to fix a problem that architecture solves for free.

## Revisit if

- Read logic in TypeScript grows complex enough to be worth centralising
- Firebase adds a genuinely fast Python cold-start path
