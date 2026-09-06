# Phase 1 · Schemas & Codegen

**~7 hours** · Status: ⬜ Not started

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

- [ ] `common/link.schema.json` — `{ type, label, url, primary }`
- [ ] `common/media.schema.json` — `{ url, alt, caption, width, height, blurhash, type }`
- [ ] `common/richtext.schema.json` — markdown string with a length cap
- [ ] `common/timeline.schema.json` — `{ displayLabel, year, durationMonths, ongoing }`
- [ ] `common/metric.schema.json` — `{ label, value, before, after, delta, highlight, icon }`
- [ ] `common/seo.schema.json` — `{ metaTitle, metaDescription, ogImageUrl, keywords }`
- [ ] `common/audit.schema.json` — `{ createdAt, updatedAt, publishedAt, createdBy }`

### 1.2 · Enums

One file each, so a new value is a one-line change that propagates everywhere.

- [ ] `project-kind` · `project-status` · `visibility`
- [ ] `skill-category` · `link-type` · `media-type` · `employment-type`

### 1.3 · Collection schemas

- [ ] `project.schema.json` — the full model from [02 · Data Model](../02-data-model.md#the-project-model)
- [ ] `profile.schema.json`
- [ ] `skill.schema.json`
- [ ] `experience.schema.json`
- [ ] `education.schema.json`
- [ ] `certification.schema.json`
- [ ] `post.schema.json`
- [ ] `contact-message.schema.json`
- [ ] `site-config.schema.json`
- [ ] `audit-log.schema.json` — `{ actor, action, collection, docId, before, after, at }`

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

- [ ] `codegen/python.yaml` → `datamodel-code-generator` → Pydantic v2
- [ ] `codegen/typescript.json` → `json-schema-to-typescript`
- [ ] `codegen/zod.mjs` → `json-schema-to-zod`
- [ ] `codegen/generate.sh` runs all three and formats the output
- [ ] `make gen` wired up
- [ ] Generated dirs marked `linguist-generated` *(already in `.gitattributes`)*

### 1.5 · Examples & validation

- [ ] 2–3 valid fixtures per schema in `examples/`
- [ ] Deliberately invalid fixtures that **must** fail validation
- [ ] A validation script over all of them
- [ ] `make validate` wired up

> The invalid fixtures matter more than the valid ones. A schema that accepts everything passes
> every valid example too.

### 1.6 · Derived artefacts

- [ ] Script generating required-field assertions into `firestore.rules`
- [ ] Script generating `firestore.indexes.json` from `x-firestore.indexes`
- [ ] Script generating `architecture/docs/ERD.md`
- [ ] `VERSIONING.md` documenting the additive/breaking policy

### 1.7 · CI drift check

- [ ] `.github/workflows/schemas.yml`
- [ ] Runs `make validate` then `make gen`, and fails on any diff
- [ ] Verified: hand-editing a generated file turns the build red

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

**`datamodel-code-generator` and `$ref` across files** — it needs `--use-schema-description` and
correct relative paths, and it's fussy about them. Get one schema working end to end before writing
the other eight.

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
