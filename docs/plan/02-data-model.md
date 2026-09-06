# 02 · Data Model

Schema-first. Every field in this project is defined exactly once, in
`architecture/schemas/`, and everything else is generated from it.

---

## The pipeline

```
                    architecture/schemas/project.schema.json
                                     │
        ┌────────────┬───────────────┼───────────────┬────────────────┐
        ▼            ▼               ▼               ▼                ▼
   Pydantic v2   TypeScript      Zod validator   Admin form     Firestore rules
   (backend)     types (FE)      (admin forms)   fields          assertions
```

| Target | Tool | Output |
|---|---|---|
| Pydantic v2 models | `datamodel-code-generator` | `backend/functions/generated/models/` |
| TypeScript types | `json-schema-to-typescript` | `frontend/src/generated/types.ts` |
| Zod validators | `json-schema-to-zod` | `frontend/src/generated/schemas.zod.ts` |
| **Admin form fields** | custom `<SchemaForm>` renderer | reads the schema at runtime |
| Rules assertions | small script | required-field checks in `firestore.rules` |
| ERD + field docs | script | `architecture/docs/` |

### Rules of the road

1. `architecture/` is the **only** place a field is ever defined.
2. `generated/` is committed but **never hand-edited**. CI runs `make gen` and fails on any diff.
3. Every schema carries `x-firestore` metadata: collection name, indexes, public-readable or not.
4. Every schema is versioned. Breaking changes ship with a migration in `backend/migrations/`.
5. `examples/` are validated in CI, so the schemas can't quietly rot.

### Why this is worth the setup cost

Adding "Podcast link" to projects is one JSON edit and `make gen`. The API validates it, TypeScript
knows about it, the admin form grows the field, and the detail page can render it. Without this,
that same change is four edits in four languages that drift apart the first time you're in a hurry.

---

## Collections

| Collection | Doc | Public read | Notes |
|---|---|---|---|
| `profile` | single doc `main` | ✅ | Name, bio, socials, résumé |
| `projects` | many | ✅ published only | The centrepiece — see below |
| `skills` | many | ✅ | Grouped by category |
| `experience` | many | ✅ | Roles, achievements |
| `education` | many | ✅ | |
| `certifications` | many | ✅ | |
| `posts` | many | ✅ published only | Blog, Phase 8 |
| `contact_messages` | many | ❌ never | Write via API only |
| `site_config` | single doc `main` | ✅ | Feature flags |
| `audit_log` | many | ❌ never | Who changed what, when |

Every content collection carries `visibility` and `order`. Public queries filter
`visibility == "public"` and sort by `order`, so you can draft live without anything showing.

---

## The project model

Rebuilt from the ground up. The old `startDate`/`endDate` pair was meaningless for projects, and the
model was far too thin to tell a story.

**Design rule: 6 required fields. Everything else optional — and the UI renders a section only when
you've filled it in.** An empty project is still a valid project; a fully-filled one is a case study.

```jsonc
{
  // ─── required (6) ───────────────────────────────────────────
  "slug": "realtime-inventory-sync",
  "title": "Realtime Inventory Sync",
  "summary": "One or two lines. This is the card text.",
  "kind": "professional",        // professional | personal | open-source
                                 // academic | freelance | experiment
  "status": "shipped",           // concept | in-progress | shipped
                                 // maintained | archived
  "visibility": "public",        // public | unlisted | draft

  // ─── timeline — replaces start/end dates ────────────────────
  "timeline": {
    "displayLabel": "2025 · 4 months",   // free text; wins over everything else
    "year": 2025,
    "durationMonths": 4,
    "ongoing": false
  },

  // ─── the story. every block optional, renders if present ────
  "content": {
    "overview":  "richtext",
    "problem":   "what was broken, and who it hurt",
    "approach":  "what you built, and why that way",
    "architecture": {
      "description": "…",
      "diagramUrl": "…",
      "components": [{ "name": "Ingest worker", "role": "…", "tech": "Python" }]
    },
    "challenges": [{ "title": "Clock skew across regions", "detail": "…" }],
    "outcomes":   [{ "label": "p95 latency", "before": "800ms",
                     "after": "120ms", "delta": "-85%", "highlight": true }],
    "learnings":  ["…"],
    "futureWork": ["…"]
  },

  // ─── tech ───────────────────────────────────────────────────
  "stack": [{ "name": "FastAPI", "category": "backend", "primary": true }],
  "tags":  ["realtime", "distributed-systems"],

  // ─── context ────────────────────────────────────────────────
  "role":  "Backend lead",
  "team":  { "size": 4, "myScope": "API design + data pipeline" },
  "client":{ "name": "…", "logoUrl": "…", "confidential": true },

  // ─── media ──────────────────────────────────────────────────
  "cover":   { "url": "…", "alt": "…", "blurhash": "…", "width": 1600, "height": 900 },
  "gallery": [{ "url": "…", "alt": "…", "caption": "…", "type": "image" }],
  "video":   { "url": "…", "provider": "youtube", "thumbnailUrl": "…" },

  // ─── links: an array, so new kinds need no schema change ────
  "links": [{ "type": "repo", "label": "Source", "url": "…", "primary": true }],
           // live | repo | docs | case-study | demo | paper | store | article | video

  // ─── social proof ───────────────────────────────────────────
  "testimonial":   { "quote": "…", "author": "…", "role": "…", "avatarUrl": "…" },
  "metrics":       [{ "label": "monthly users", "value": "12k", "icon": "users" }],
  "awards":        [{ "title": "…", "issuer": "…", "year": 2025, "url": "…" }],
  "collaborators": [{ "name": "…", "role": "…", "url": "…" }],

  // ─── publishing ─────────────────────────────────────────────
  "featured": true, "order": 1, "pinned": false,
  "seo": { "metaTitle": "…", "metaDescription": "…",
           "ogImageUrl": "…", "keywords": ["…"] },
  "readingMinutes": 4,
  "createdAt": "…", "updatedAt": "…", "publishedAt": "…"
}
```

### Three things worth calling out

**`timeline.displayLabel` beats structured dates.** Real projects have fuzzy edges — "2024–25",
"a weekend", "ongoing since 2023". A free-text label you control renders correctly every time;
`year` and `durationMonths` exist alongside it purely for sorting and filtering.

**`client.confidential: true`** renders "a logistics client" instead of the name, and the name is
never sent to the browser — it's stripped server-side, not hidden with CSS. This is what lets you
show employer work without leaking anything.

**`links` is an array, not an object.** A fixed `{ live, repo, demo }` object needs a schema change
every time a new kind of link comes along. An array of `{ type, label, url }` doesn't.

### Progressive disclosure

The detail page walks the object and renders only the blocks that exist. Three filled fields gives a
clean short page; twenty gives a full case study. No empty headings, no `null` placeholders, no
"coming soon".

The admin form does the same in reverse: required fields up top, everything else in collapsible
"add a section" panels — so it never feels like a 40-field wall.

---

## The other collections

Same treatment: a small required core, plus optional extras that only render when filled.

**`skill`** — required: `name`, `category`, `level` (1–5).
Optional: `yearsOfExperience`, `icon`, `projectsUsedIn[]`, `certificationUrl`, `blurb`, `featured`.

**`experience`** — required: `company`, `role`, `startDate`, `current`.
Optional: `endDate`, `location`, `employmentType`, `highlights[]` (achievements with numbers),
`techStack[]`, `companyLogoUrl`, `companyUrl`, `promotions[]`, `teamSize`.

> Note: start/end dates **do** make sense here — a job genuinely has a start and an end.
> That's why experience keeps them and projects don't.

**`profile`** — name, headline, tagline, bio, location, email, avatar, OG image, résumé URL,
`socials[]`, `availableForWork`.

**`contact_message`** — `name`, `email`, `subject`, `message`, plus server-set `createdAt`, `ip`,
`userAgent`, `spamScore`, `read`, `replied`.

Full definitions get written in [Phase 1](./phases/phase-1-schemas.md).

---

## Versioning & migration

Each schema declares `"x-version": "1.0.0"`.

- **Additive change** (new optional field) — bump minor, no migration. This is most changes.
- **Breaking change** (rename, type change, new required field) — bump major, write
  `backend/migrations/NNN_description.py`, and run it against the emulator before prod.
- Migrations are idempotent and logged to `audit_log`.

---

**Next:** [03 · Security](./03-security.md)
