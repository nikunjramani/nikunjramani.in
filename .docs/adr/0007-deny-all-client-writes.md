# 0007 · All client writes denied, including admin

**Status:** ✅ Accepted · **Date:** 2026-09-06

---

## Context

Firebase's usual pattern is a client that talks to Firestore directly, with security rules deciding
what's allowed. For an admin panel that would mean: sign in, get the `admin` claim, and let
Firestore rules permit writes from the browser.

That works, but it means the browser holds credentials capable of mutating the database. Any XSS bug
becomes a data-integrity bug. It also puts validation, rate limiting and audit logging in a place
where they can be bypassed by anyone willing to open a console.

## Decision

**Firestore security rules deny all client writes — for everyone, including the admin.**

```js
allow read:  if resource.data.visibility == 'public';
allow write: if false;
```

Every mutation goes through the Python API, which verifies a Firebase ID token, asserts the
`admin: true` custom claim, validates against the generated models, applies business rules, and
writes an audit record.

## Consequences

### What this makes easier

- The security rule is one line and impossible to get subtly wrong. Complex rules are where
  Firebase security bugs live
- Validation, rate limiting, business rules and audit logging apply to **every** mutation with no
  bypass
- XSS in the admin panel can't corrupt data — the browser holds no write capability
- Server-side hooks (cache revalidation, image processing, audit trail) are guaranteed to run
- Contact-form spam filtering has a place to live

### What this makes harder — the cost we're accepting

- **One extra network hop on every save.** Roughly 100–300ms warm, 1–3s on a cold start
- No Firestore real-time listeners for admin writes; the UI updates optimistically instead
- Offline editing is off the table
- The API must implement every CRUD operation rather than getting them free from the SDK

The save latency is the honest cost. Behind a spinner on a form submit it's unobjectionable — and
it only applies to one user, once in a while.

## Alternatives considered

### Rules-based admin writes
The conventional Firebase pattern, less code. Rejected: puts credentials in the browser and makes
validation and audit optional rather than guaranteed.

### Hybrid — simple writes client-side, complex ones via API
Rejected as the worst of both. Two write paths means two sets of rules, and "which path does this go
through?" becomes a question you have to answer on every change.

## Revisit if

- Save latency becomes genuinely annoying in daily use
- A real offline-editing requirement appears
