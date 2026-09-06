---
name: add-schema-field
description: Add or change a field on any content model (project, skill, experience, profile, post). Use whenever a new field, enum value, or model shape is needed — this project generates all models from JSON Schema, so editing a Pydantic model or TypeScript type by hand is always wrong.
---

# Adding or changing a schema field

`architecture/schemas/` is the only place a field is ever defined. Everything else is generated.

## Never do this

- ❌ Edit a file under `frontend/src/generated/` or `backend/functions/generated/`
- ❌ Add a field to a Pydantic model or TypeScript interface directly
- ❌ Add a form input to the admin panel by hand

All four are generated from the schema. CI fails on drift. → [ADR 0006](../../../docs/adr/0006-json-schema-source-of-truth.md)

## Steps

**1 · Edit the schema**

`architecture/schemas/<model>.schema.json`. Default to **optional** — this project's models are a
small required core plus many optional fields that render only when filled.

```jsonc
"podcastUrl": {
  "type": "string",
  "format": "uri",
  "description": "Link to a podcast episode about this project"
}
```

Add to `required` only if the model is genuinely invalid without it. Adding a required field is a
**breaking change** — see Versioning below.

Reuse `common/` definitions rather than inlining shapes:

```jsonc
"cover": { "$ref": "./common/media.schema.json" }
```

New enum value? Edit `architecture/enums/<name>.json`, not the schema.

**2 · Update the index if needed**

Adding a field that gets queried or sorted means a new Firestore index:

```jsonc
"x-firestore": { "indexes": [["visibility", "order"], ["visibility", "featured", "order"]] }
```

**3 · Regenerate**

```bash
make gen
```

Produces the Pydantic model, TypeScript type and Zod validator. Never edit its output.

**4 · Add an example**

`architecture/examples/` — a fixture exercising the new field, plus an invalid one that must be
rejected. The invalid fixture matters more; a schema that accepts everything passes every valid
example too.

```bash
make validate
```

**5 · Use it**

- **Public page** — render conditionally. `{project.podcastUrl && <PodcastLink … />}`. Never an
  empty heading.
- **Admin form** — usually nothing to do. `<SchemaForm>` reads the schema and renders the control.
  Only touch it if the field needs a control that doesn't exist yet.
- **API** — usually nothing to do. Generated models validate automatically. Only touch a service if
  the field carries business rules.

**6 · Commit schema and generated output together**

They must never be in separate commits, or a checkout in between has stale generated code.

## Versioning

| Change | Version | Migration |
|---|---|---|
| New optional field | minor | none |
| New enum value | minor | none |
| Rename, retype, or new required field | **major** | `backend/migrations/NNN_*.py` |

Migrations are idempotent, logged to `audit_log`, and run against the emulator first.

## Verify

```bash
make gen && git diff --exit-code   # must be clean after committing
make validate
make test
```

The end-to-end check: the field exists in the Pydantic model, the TS type, the Zod validator and the
admin form — with no hand-editing anywhere.
