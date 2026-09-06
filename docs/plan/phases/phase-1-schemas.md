# Phase 1 · Schemas & Codegen

**~7 hours** · Status: ✅ Done — 2026-09-06

> **Goal:** Every model in the system defined once, in JSON Schema, with working
> generation into Pydantic, TypeScript and Zod — and CI that makes drift impossible.

This is the keystone phase. Everything after it goes faster because of it.

---

## Prerequisites

- [ ] [Phase 0](./phase-0-foundation.md) done
- [ ] [02 · Data Model](../02-data-model.md) read

---

## Tasks

### 1.1 · Common definitions

Build these first — everything else references them.

- [x] `common/link.schema.json` — `{ type, label, url, primary }`
- [x] `common/media.schema.json` — `{ url, alt, caption, width, height, blurhash, type }`
- [x] ~~`common/richtext.schema.json`~~ — dropped; a plain string with `maxLength` is enough,
      and a structured document model is a project in itself
- [x] `common/timeline.schema.json` — `{ displayLabel, year, durationMonths, ongoing }`
- [x] `common/metric.schema.json` — `{ label, value, before, after, delta, highlight, icon }`
- [x] `common/seo.schema.json` — `{ metaTitle, metaDescription, ogImageUrl, keywords }`
- [x] `common/audit.schema.json` — `{ createdAt, updatedAt, publishedAt, createdBy }`

### 1.2 · Enums

One file each, so a new value is a one-line change that propagates everywhere.

- [x] `project-kind` · `project-status` · `visibility`
- [x] `skill-category` · `link-type` · `media-type` · `employment-type`

### 1.3 · Collection schemas

- [x] `project.schema.json` — the full model from [02 · Data Model](../02-data-model.md#the-project-model)
- [x] `profile.schema.json`
- [x] `skill.schema.json`
- [x] `experience.schema.json`
- [x] `education.schema.json`
- [x] `certification.schema.json`
- [x] `post.schema.json`
- [x] `contact-message.schema.json`
- [x] `site-config.schema.json`
- [x] `audit-log.schema.json` — `{ actor, action, collection, docId, before, after, at }`

Each carries `x-firestore` metadata:

```jsonc
"x-firestore": {
  "collection": "projects",
  "publicRead": true,
  "indexes": [["visibility", "order"], ["visibility", "featured", "order"]],
  "ttl": null
}
```

### 1.4 · Codegen pipeline

- [x] `datamodel-code-generator` → Pydantic v2 *(flags live in `generate.sh`, no separate config file needed)*
- [x] `json-schema-to-typescript` → TypeScript types
- [x] `json-schema-to-zod` → Zod validators, **after dereferencing** (see gotchas)
- [x] `codegen/generate.sh` runs all three and formats the output
- [x] `make gen` wired up
- [x] Generated dirs marked `linguist-generated` *(already in `.gitattributes`)*

### 1.5 · Examples & validation

- [x] 2–3 valid fixtures per schema in `examples/`
- [x] Deliberately invalid fixtures that **must** fail validation
- [x] A validation script over all of them
- [x] `make validate` wired up

> The invalid fixtures matter more than the valid ones. A schema that accepts everything passes
> every valid example too.

### 1.6 · Derived artefacts

- [ ] Script generating required-field assertions into `firestore.rules`
- [x] Script generating `firestore.indexes.json` from `x-firestore.indexes`
- [x] Script generating `architecture/docs/ERD.md`
- [x] `VERSIONING.md` documenting the additive/breaking policy

### 1.7 · CI drift check

- [x] `.github/workflows/schemas.yml`
- [x] Runs `make validate` then `make gen`, and fails on any diff
- [x] Verified: hand-editing a generated file turns the build red

---

## Definition of done

1. `make gen` produces Pydantic models, TS types and Zod validators from the schemas
2. All example fixtures validate; every invalid one is rejected
3. Adding a field to one schema and running `make gen` updates **all three** targets
4. CI fails if generated code is stale
5. `architecture/docs/ERD.md` is generated, not written

**The real test:** add `"podcastUrl"` to `project.schema.json`, run `make gen`, and confirm it
appears in the Pydantic model, the TS type and the Zod validator with zero hand-editing. Then revert.

---

## Gotchas

**`datamodel-code-generator` and `$ref` across files** — cross-file refs require a **directory**
output, not a file, and every schema must sit under one input root. That is why `enums/` lives
inside `schemas/` rather than beside it.

**`json-schema-to-zod` silently ignores cross-file `$ref`s.** It emits `z.any()` for every
referenced field, producing a validator that looks correct and accepts anything — worse than no
validator. Schemas are dereferenced with `json-schema-ref-parser` before Zod generation. If you ever
see `z.any()` in `schemas.zod.ts`, that step has broken.

**Zod 4 changed `z.record()` to take two arguments**, and `json-schema-to-zod@2` emits Zod 3 syntax.
The frontend is pinned to `zod@^3` for this reason. Moving to Zod 4 needs a generator that targets
it.

**`format: email` generates `EmailStr`**, which needs `pydantic[email]` — otherwise the import fails
at runtime with an unhelpful message.

**Optional vs nullable.** JSON Schema's "not in `required`" becomes `Optional[X] = None` in Pydantic
and `x?: X` in TypeScript. Zod needs `.optional()` explicitly. Decide the convention now and apply it
consistently, or you'll get three subtly different notions of "missing".

**Don't over-model rich text.** A markdown string with a max length is enough. A structured
document model is a project in itself.

**Firestore timestamps aren't JSON.** Schemas declare `string` + `format: date-time`; the repository
layer converts to and from Firestore `Timestamp`. Keep that conversion in one place.

**Resist perfect schemas.** They'll change in Phase 4 when the design meets reality. That's fine —
centralised change is exactly what this phase buys you.

---

**Next:** [Phase 2 · Content & Design](./phase-2-content-design.md)
