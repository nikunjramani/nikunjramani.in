# 0016 · Build standard content domains from their model; keep Firestore in repositories

**Status:** ✅ Accepted — refines [0011](./0011-domain-wise-separate-functions.md) and [0012](./0012-generic-content-crud-in-shared.md)
**Date:** 2026-10-13
**Deciders:** Nikunj Ramani

---

## Context

ADR 0012 moved content CRUD's business rules into `shared/crud.py`, but every content domain
still kept its own `repository.py`, `service.py` and `routes.py`. For seven of the eight
(skills, experience, education, certifications, posts, profile, settings) those three files were
about 40 lines that differed only in a model name, a collection name and a slugged/singleton
flag. ADR 0011's rule — each domain owns routes, service and repository — was being honoured in
shape only.

Separately, rule 6 says repositories are the only code that touches the Firestore SDK. In
practice `SystemService`, the nightly backup and `AuditService` all queried Firestore directly.

## Decision

`shared.crud.content_domain(model, collection=..., slugged=..., singleton_id=...)` builds a
standard domain's repository class, service factory and router. Such a domain is now a single
`__init__.py` that calls it and passes the router to `make_function`. ADR 0011's deploy
isolation is unchanged: still one package, one function and one `FUNCTION_TARGET` per domain,
and import-linter still checks each one. A domain with real domain-specific logic (`projects`,
with `duplicate`) keeps hand-written files.

Firestore access lives in repositories, including shared ones: `shared/repositories/audit.py`
for the audit log, `shared/repositories/references.py` for "which content mentions this URL",
and `src/system/repository.py` for backups. The one exception is `shared/core/rate_limit.py`.
Its check-and-increment is a single transaction, and splitting it across a service and a
repository would make it non-atomic.

## Consequences

### What this makes easier

- Adding a standard content domain is one file plus the four registrations in
  `tests/test_domain_registry.py`, which now fails if any of them is missed.
- Services can be tested with no Firestore SDK in scope.

### What this makes harder — the cost we're accepting

- A content domain's repository class is created at runtime. Tests reach it as
  `src.<domain>.domain.repository` rather than by importing a named class.
- When a domain outgrows the factory, it has to be expanded back into files. That's
  mechanical, since `projects` is the template.

## Alternatives considered

### Keep the boilerplate files
They added no isolation and only gave a fix one more place to miss.

### One function for all content domains
That's ADR 0003, which 0011 superseded for cold-start and blast-radius reasons.

## Revisit if

- Several content domains grow their own logic, at which point explicit files read better.
