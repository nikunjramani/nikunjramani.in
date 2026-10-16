# Schema and codegen decisions

Root: [architecture/](../../architecture/). Flow: [CODE_FLOW §10](../CODE_FLOW.md#10--schemas-and-codegen).
Entries SC-01…SC-07 were backfilled on 2026-10-16.

### SC-01 · JSON Schema is the only definition of a model

- **Where:** [architecture/schemas/](../../architecture/schemas/), [codegen/generate.sh](../../architecture/codegen/generate.sh) (`make gen`)
- **Decision:** Pydantic models, TS types, Zod validators, admin form schemas, Firestore indexes,
  the public-read rules block and the ERD are all generated and committed; CI regenerates and fails
  on any diff.
- **Why:** two hand-maintained model sets (Python and TS) drift silently; a schema read by both can't.
- **Related:** ADR 0006

### SC-02 · `additionalProperties: false` everywhere — so no model has an `id`

- **Why:** an unknown field is a bug, not data. The id is the document's key, carried beside the
  model (BE-12, FE-06).

### SC-03 · Firestore behaviour is declared in the schema (`x-firestore`)

- **Where:** each schema's `x-firestore`: `collection`, `publicRead`, `indexes`, `ttlField`;
  [gen-indexes.py](../../architecture/codegen/gen-indexes.py), [gen-rules.py](../../architecture/codegen/gen-rules.py)
- **Why:** the query, its index, its TTL and whether the public may read it belong next to the shape
  they describe. A collection without a schema that still needs a TTL (`_rate_limits`) is listed in
  `gen-indexes.py` itself.

### SC-04 · `architecture/api-routes.json` is the manifest of HTTP subdomains

- **Where:** [api-routes.json](../../architecture/api-routes.json) → `frontend/src/generated/api-routes.ts`
  → `next.config.ts` rewrites and `lib/contact.ts`; checked by `tests/test_domain_registry.py`
- **Why:** the frontend's routes, the backend's functions and Terraform's invoker list must agree;
  one manifest plus a test makes disagreement a failing test instead of a production 404.
- **Since:** 2026-10-13

### SC-05 · Every constraint has an invalid fixture

- **Where:** [architecture/examples/invalid/](../../architecture/examples/invalid/), `make validate`
- **Why:** a schema that accepts everything passes every valid example; only a must-fail fixture
  proves the constraint exists.

### SC-06 · Optional by default; required fields are a major version

- **Where:** [architecture/VERSIONING.md](../../architecture/VERSIONING.md)
- **Why:** content models are a small required core plus optional fields that render only when
  filled (ADR 0008); a new required field invalidates every existing document and needs a migration.

### SC-07 · Every publicly readable document carries `visibility`, required by the schema

- **Why:** the rules read `resource.data.visibility`; a document without it is denied and the page
  renders empty with no useful error — including the singletons `profile/main` and `site_config/main`.
