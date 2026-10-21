---
paths:
  - "architecture/**"
  - "backend/shared/generated/**"
  - "frontend/src/generated/**"
---

# Schema and codegen rules

`architecture/schemas/` is the only place a field or model is defined (ADR 0006). Use the
`add-schema-field` skill. Decisions: `.docs/decisions/schemas-codegen.md`.

- **Never hand-edit generated output**: `backend/shared/generated/`,
  `frontend/src/generated/`, `infra/rules/firestore.indexes.json`, the generated block of
  `infra/rules/firestore.rules`, `architecture/docs/ERD.md`. Edit the schema, run `make gen`, and
  commit schema + output together. CI fails on drift.
- **Default new fields to optional.** A new required field is a major version with a migration
  (`architecture/VERSIONING.md`).
- **Every schema sets `additionalProperties: false`** — which is why no model has an `id`; the id
  travels beside the data (`Record`, `WithId`).
- **Every publicly readable document carries `visibility`** — rules deny reads where it's missing.
- **Firestore behaviour lives in `x-firestore`**: `collection`, `publicRead`, `indexes`
  (`"field:desc"`, `"tags:contains"`), `ttlField`. Add the index when you add the query.
- **Add an invalid fixture** under `architecture/examples/invalid/` with any constraint — a schema
  that accepts everything passes every valid example too.
- **`architecture/api-routes.json`** is the manifest of HTTP subdomains; it generates
  `frontend/src/generated/api-routes.ts` and is checked against deploys by
  `tests/test_domain_registry.py`.
- `make validate` checks schemas and fixtures; `make gen && git diff --exit-code` must be clean.
