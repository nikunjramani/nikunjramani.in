# 0006 · JSON Schema as the single source of truth

**Status:** ✅ Accepted · **Date:** 2026-09-06

---

## Context

The same data shapes are needed in at least five places:

1. Pydantic models for API validation (Python)
2. TypeScript types for the frontend
3. Zod schemas for admin form validation
4. The admin form fields themselves
5. Required-field assertions in Firestore rules

Hand-maintaining five representations of `Project` guarantees drift. Not eventually — the first time
a field is added in a hurry.

This matters more here than usual because the project model is deliberately large and mostly
optional ([0008](./0008-projects-drop-start-end-dates.md)), so it *will* change often.

## Decision

**JSON Schema (draft 2020-12) files in `architecture/schemas/` are the only place a field is ever
defined.** Everything else is generated.

```
architecture/schemas/project.schema.json
        ├─▶ Pydantic v2 models      datamodel-code-generator
        ├─▶ TypeScript types        json-schema-to-typescript
        ├─▶ Zod validators          json-schema-to-zod
        ├─▶ Admin form fields       <SchemaForm> reads the schema at runtime
        └─▶ Firestore rules assertions
```

Generated code is committed but never hand-edited. CI runs `make gen` and fails on any diff.

## Consequences

### What this makes easier

- Adding a field is one JSON edit plus `make gen`. It then exists in the API, the types, the
  validators and the admin form
- Backend and frontend literally cannot disagree about a shape
- The admin panel gets dramatically cheaper — forms build themselves from the schema
- Schemas double as documentation, and an ERD can be generated from them
- Migration policy has an obvious home

### What this makes harder — the cost we're accepting

- **Roughly a day of setup** before any feature work happens (Phase 1)
- JSON Schema is verbose and less pleasant to write than Pydantic classes
- `$ref` across files is fussy in the generators; expect an hour of fighting paths
- One more build step, and a CI check that will occasionally annoy you
- Codegen output isn't always idiomatic in either language

### Why it's worth it anyway

The alternative isn't "no cost" — it's paying the cost repeatedly, in small amounts, forever, plus
the debugging time when the two sides quietly disagree.

## Alternatives considered

### Pydantic as the source, generate TypeScript from OpenAPI
Nicer to author. Rejected: it can't generate the admin form fields or the Zod validators cleanly,
and makes Python the centre of gravity for a frontend concern.

### TypeScript/Zod as the source, generate Python
Same problem, mirrored.

### Hand-maintain both
Fine for two or three fields. The project model has around forty.

## Revisit if

- The generators prove too limiting for a shape we actually need
- Schema authoring becomes the bottleneck rather than the accelerator
