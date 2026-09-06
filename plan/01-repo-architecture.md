# 01 · Repo Architecture

Folder layout, and the layering rules that keep it from turning to mud.

---

## Top level

```
nikunjramani.in/
├── README.md · Makefile · .gitignore · .gitattributes · .editorconfig
├── architecture/     # JSON Schemas — source of truth
├── frontend/         # Next.js 16
├── backend/          # Python 3.13 Firebase Functions
├── infra/            # Terraform + security rules
├── docs/             # CONTENT.md · DESIGN.md · RUNBOOK.md · ADR/
├── plan/             # these documents
└── .github/workflows/
```

Four roots that can each be built, tested and deployed independently. That's what lets CI use path
filters so a copy tweak doesn't rebuild the Python functions.

---

## `architecture/`

```
architecture/
├── schemas/
│   ├── common/                   # $defs reused everywhere
│   │   ├── link.schema.json          media.schema.json
│   │   ├── richtext.schema.json      timeline.schema.json
│   │   ├── metric.schema.json        seo.schema.json
│   │   └── audit.schema.json         # createdAt / updatedAt / createdBy
│   ├── profile.schema.json           project.schema.json
│   ├── skill.schema.json             experience.schema.json
│   ├── education.schema.json         certification.schema.json
│   ├── post.schema.json              contact-message.schema.json
│   └── site-config.schema.json
├── enums/                        # one file per enum, referenced by schemas
│   ├── project-kind.json  project-status.json  skill-category.json
│   ├── link-type.json     visibility.json      media-type.json
├── examples/                     # valid + intentionally-invalid fixtures
├── codegen/
│   ├── generate.sh               # what `make gen` runs
│   ├── python.yaml               # datamodel-code-generator config
│   ├── typescript.json           # json-schema-to-typescript config
│   └── zod.mjs                   # json-schema-to-zod
├── docs/ERD.md                   # generated
└── VERSIONING.md
```

Full explanation in [02 · Data Model](./02-data-model.md).

---

## `frontend/`

```
frontend/
├── src/
│   ├── app/
│   │   ├── (site)/                        # public, server-rendered
│   │   │   ├── page.tsx                   # /
│   │   │   ├── projects/page.tsx
│   │   │   ├── projects/[slug]/page.tsx
│   │   │   ├── about/  experience/  contact/  blog/
│   │   │   └── layout.tsx                 # nav + footer
│   │   ├── (admin)/admin/                 # private, client-rendered
│   │   │   ├── layout.tsx                 # auth guard
│   │   │   ├── page.tsx                   # dashboard
│   │   │   ├── projects/[id]/page.tsx
│   │   │   └── skills/ experience/ media/ messages/ settings/
│   │   ├── api/revalidate/route.ts        # on-demand ISR bust
│   │   ├── sitemap.ts  robots.ts  opengraph-image.tsx
│   │   └── layout.tsx  not-found.tsx
│   ├── components/
│   │   ├── ui/                            # shadcn primitives
│   │   ├── site/                          # Hero, ProjectCard, Timeline, SkillGrid…
│   │   ├── admin/                         # SchemaForm, MediaPicker, ReorderList…
│   │   └── seo/                           # JsonLd, MetaTags
│   ├── lib/
│   │   ├── firebase/{admin,client,auth}.ts
│   │   ├── data/                          # one query module per collection
│   │   ├── api/                           # typed client for the Python API
│   │   └── utils/
│   ├── generated/                         # ⚠ codegen output — never hand-edit
│   │   └── types.ts  schemas.zod.ts
│   ├── hooks/  styles/  config/
├── public/
├── next.config.ts  tailwind.config.ts  tsconfig.json
└── apphosting.yaml                        # App Hosting build + runtime config
```

### Route groups matter

`(site)` and `(admin)` are Next.js route groups — parentheses mean they don't appear in the URL, but
they get **separate layouts and separate bundles**. The admin editor, its form renderer and the
Firebase client SDK never ship to a visitor reading a project page.

---

## `backend/`

```
backend/functions/
├── main.py                        # entrypoint: exports every function
├── api/
│   ├── app.py                     # FastAPI app factory
│   ├── deps.py                    # auth, pagination, rate-limit dependencies
│   └── routers/
│       ├── public/{contact,resume,health}.py
│       └── admin/{projects,skills,experience,education,certifications,
│                  posts,profile,media,messages,settings}.py
├── triggers/
│   ├── on_contact_created.py      # → Resend email + spam score
│   ├── on_media_uploaded.py       # → WebP + thumbnails + blurhash
│   └── on_content_published.py    # → revalidate Next.js cache
├── scheduled/
│   ├── nightly_backup.py          # Firestore → Storage JSON
│   └── weekly_digest.py           # optional
├── core/
│   ├── config.py                  # pydantic-settings
│   ├── firebase.py  security.py  errors.py  logging.py
│   └── rate_limit.py
├── services/                      # firestore · storage · email · image · seo
├── repositories/                  # one per collection + a generic base
├── generated/models/              # ⚠ codegen output — never hand-edit
├── tests/{unit,integration}/
└── pyproject.toml  requirements.txt  .env.example
```

---

## Layering rules

### Backend — strict one-way dependency

```
router  →  service  →  repository  →  Firestore
   ↑          ↑            ↑
   └──── generated Pydantic models ────┘
```

| Layer | Does | Must never |
|---|---|---|
| **Router** | Parse the request, authorize, delegate, serialize | Contain business logic or touch Firestore |
| **Service** | Business rules: slug uniqueness, publish transitions, reordering, cache busting | Know what HTTP is |
| **Repository** | All Firestore SDK calls, via a generic `BaseRepository[T]` | Contain business rules |

`BaseRepository[T]` gives every collection CRUD, pagination and ordering for free, so a new
collection is a subclass and a schema — not a new file of boilerplate.

**No hand-written models, ever.** They come from `architecture/`.

### Frontend

```
page (server)  →  lib/data/*  →  Firebase Admin SDK      ← reads
page (client)  →  lib/api/*   →  Python API              ← writes
```

- Server Components fetch data. Client Components handle interaction only. Push `"use client"` as
  deep into the tree as possible — the further down it goes, the less JS ships.
- `lib/data/` is the **only** place Firestore is queried. Components never import the SDK.
- Nothing in `(site)/` may import from `(admin)/`. Enforced by an ESLint boundary rule, because
  this is the kind of thing that silently regresses.

---

## The Makefile

One entry point per task, and CI runs the exact same targets — so "works locally, fails in CI" has
one less cause.

```makefile
make setup     # install frontend + backend dependencies
make dev       # Next.js dev server + Firebase emulators
make gen       # regenerate all models from architecture/schemas
make lint      # eslint + ruff + mypy + terraform fmt
make test      # vitest + pytest
make build     # production build of both
make deploy    # terraform apply + firebase deploy
make clean
```

---

**Next:** [02 · Data Model](./02-data-model.md)
