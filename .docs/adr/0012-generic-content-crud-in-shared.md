# 0012 · Generic content CRUD lives in shared/, not per domain

**Status:** ✅ Accepted
**Date:** 2026-09-22
**Deciders:** Nikunj Ramani

---

## Context

Eight domains — `projects`, `skills`, `experience`, `education`, `certifications`, `posts`,
`profile`, `settings` — need the same admin operations: create, list, get, partial update,
delete, reorder. And underneath the CRUD verbs, they need the same *business rules* too:
every mutation writes a before/after snapshot to `audit_log`; a visibility change from
non-public to `public` is a "publish" event with a `publishedAt` timestamp that must not
move on republish; a write that changes public content should bust the Next.js ISR cache.

[ADR 0011](./0011-domain-wise-separate-functions.md) splits the backend into one deployed
function per domain specifically so a domain's code, cold start and blast radius are
independent of every other domain's. Read uncritically, that could be taken to mean each
domain's logic should be hand-written independently too. It shouldn't: ADR 0011 is about
*deploy* isolation — separate containers, separate `FUNCTION_TARGET`s, separate import
boundaries — not about forbidding eight domains from sharing infrastructure that is
genuinely identical between them. Hand-writing the same audit-trail-plus-publish-transition
logic eight times would not add isolation; it would add seven places for the ninth bug to
hide having already been fixed in the first eight.

The tell that this was really one piece of logic, not eight coincidentally similar ones,
came from having built `contact`'s service by hand in Phase 3.2 and then starting `skills`'
by hand too: the second draft was line-for-line the same shape as the first, differing only
in which Pydantic model and which Firestore collection it closed over.

## Decision

`shared/crud.py` holds `ContentService[T]` (the business rules above, generic over any
Pydantic model backed by a `BaseRepository[T]`) and `make_crud_router()` (a FastAPI router
factory producing the collection routes — `GET/POST /`, `GET/PATCH/DELETE /{id}`,
`POST /reorder` — or, for `profile` and `settings`, the singleton routes —
`GET/PUT/PATCH /` on one fixed document id).

A domain that needs nothing beyond the generic behaviour is three files:

```python
# src/skills/repository.py
class SkillRepository(BaseRepository[Skill]):
    collection = "skills"
    model = Skill

# src/skills/service.py
class SkillService(ContentService[Skill]):
    def __init__(self, db=None, *, repo=None):
        super().__init__(repo if repo is not None else SkillRepository(db))

# src/skills/routes.py
router.include_router(make_crud_router(model=Skill, get_service=get_skills_service))
```

A domain that needs more — `projects.duplicate()`, say — subclasses `ContentService` and
adds exactly that, with everything else still coming from the base class.

## Consequences

### What this makes easier

- Adding a ninth content domain is repository + one-line service + one line of router
  wiring, not a business-logic rewrite
- The audit trail, publish transitions and merge-patch semantics are tested once
  (`shared/tests/test_crud.py`, 22 tests) rather than trusted to be right in eight separate,
  independently-written implementations
- A bug found in one domain's CRUD behaviour is a bug found — and fixed — in all of them
- Router wiring itself is proven once per *shape* (four-domain collection parametrised in
  `tests/test_domain_routers.py`, two-domain singleton in `tests/test_singleton_routers.py`),
  rather than trusted by eye at each of the eight call sites

### What this makes harder — the cost we're accepting

- `shared/` now holds actual business logic, not just infrastructure (Firestore access,
  auth, logging) the way [ADR 0011](./0011-domain-wise-separate-functions.md) originally
  framed it. The line between "infrastructure eight domains share" and "a domain's own
  rules" needs judgement, not a mechanical test
- A change to `shared/crud.py` redeploys every domain that uses it — already true of
  `shared/` generally, but this makes it a larger, more central piece to be careful editing
- The generic router factory's admin-only assumption is baked in: there is deliberately no
  way to build a public route through `make_crud_router`, so a domain needing a mixed
  public/admin surface (`contact`, `media`) still writes its own routes by hand

### Where the line is drawn

Cross-domain tests for this shared logic live in a new top-level `backend/functions/tests/`,
not under `shared/tests/`, because they import from several `src.<domain>` packages to
exercise the wiring — and `shared/` importing from `src/` is exactly what
[ADR 0011](./0011-domain-wise-separate-functions.md)'s import-linter contract forbids. The
contract caught this itself the first time these tests landed in the wrong place, which is
the mechanism working as intended, not a gap in it.

## Alternatives considered

### Hand-write each domain's service independently (the original plan)
What Phase 3.2 built for `contact`, and what `skills` started as. Rejected on the evidence:
the second hand-written service was a near copy of the first, which is exactly the signal
that the logic belongs in one place.

### A base class with abstract hooks, subclassed per domain
More "OO-correct," but subclasses only override behaviour they need to differ, and none of
the eight actually need to differ in the CRUD path itself. `ContentService` composition
(wrap a `BaseRepository`) plus targeted subclassing where genuinely needed (`ProjectService`)
gets the same result with less ceremony.

### Put the shared logic in `BaseRepository` itself
Rejected: `BaseRepository` is Firestore access — CRUD *storage*, no business rules, and
[ADR 0011](./0011-domain-wise-separate-functions.md) already draws that line. Audit trail
and publish transitions are business rules; they belong one layer up, in a service.

## Revisit if

- A domain's requirements diverge from the generic shape often enough that the subclass
  hook points stop being enough and every domain ends up overriding most of it anyway
- `shared/crud.py` grows past what one file should hold — split by concern (audit, publish
  transitions, merge) rather than abandoning the shared-service idea
