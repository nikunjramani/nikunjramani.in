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
├── docs/
│   ├── adr/          # architecture decision records — one file per decision
│   ├── plan/         # these documents
│   ├── CONTENT.md    # the site's actual copy
│   ├── DESIGN.md     # design tokens and rules
│   └── RUNBOOK.md    # deploy, rollback, rotate secrets, restore
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
├── main.py                        # imports + re-exports every function
│
├── shared/                        # imported by every domain; owns nothing itself
│   ├── core/
│   │   ├── config.py              # pydantic-settings
│   │   ├── firebase.py  security.py  errors.py  logging.py
│   │   └── rate_limit.py
│   ├── api.py                     # make_function(): FastAPI + a2wsgi wrapper, written once
│   ├── repositories/base.py       # BaseRepository[T]
│   ├── services/                  # storage · email · image · audit
│   └── generated/models/          # ⚠ codegen output — never hand-edit
│
└── src/                           # one directory per domain = one deployed function
    ├── contact/
    │   ├── __init__.py            # exports api_contact
    │   ├── routes.py              # FastAPI router
    │   ├── service.py             # business rules
    │   ├── repository.py          # Firestore access
    │   ├── triggers.py            # on_contact_created → email
    │   └── tests/
    ├── projects/                  # routes · service · repository · triggers · tests
    ├── skills/
    ├── experience/
    ├── education/
    ├── certifications/
    ├── posts/
    ├── profile/
    ├── media/                     # + on_media_uploaded → WebP, thumbs, blurhash
    ├── messages/
    ├── settings/
    └── system/                    # health · resume · sitemap · nightly_backup
```

Every domain has the identical shape, so adding one is copy, rename, register.
→ [ADR 0011](../adr/0011-domain-wise-separate-functions.md)

### One function per domain

Each domain exports a single deployed function through a shared wrapper:

```python
# src/projects/__init__.py
from shared.api import make_function
from .routes import router

api_projects = make_function(router, name="api_projects")
```

**Next.js rewrites** keep the API surface unified, so the frontend sees one base URL:

```ts
// frontend/next.config.ts
async rewrites() {
  return DOMAINS.map((domain) => ({
    source: `/api/v1/${domain}/:path*`,
    destination: `${FUNCTIONS_BASE}/api_${domain}/:path*`,
  }));
}
```

> Not Firebase Hosting rewrites — App Hosting is a different product and has none. Doing it in
> Next.js means the browser only ever talks to one origin, so there is no CORS preflight on any API
> call. See the implementation note in
> [ADR 0011](../adr/0011-domain-wise-separate-functions.md).

⚠️ **Adding a domain means adding a rewrite.** Forgetting produces a 404 that looks like a routing
bug.

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

### Domain boundaries

Two import rules, both non-negotiable:

- **`shared/` may never import from `src/`.** That's a circular dependency and it will bite.
- **No domain may import another domain's `service` or `repository`.** Cross-domain work goes
  through an event or through `shared/`.

Enforced in review and by an import-linter rule in `make lint`.

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
make validate  # validate schemas + example fixtures
make lint      # eslint + ruff + mypy + import-linter + terraform fmt
make test      # vitest + pytest
make build     # production build of both
make deploy    # terraform apply + firebase deploy
make clean
```

---

**Next:** [02 · Data Model](./02-data-model.md)
