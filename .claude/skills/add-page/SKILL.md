---
name: add-page
description: Add or modify a page in the Next.js frontend — public site route, admin screen, or component. Use for any frontend work, since this project has strict Server/Client Component and data-access rules that are easy to violate silently.
---

# Adding a frontend page

## Data access

```
page (server)  →  lib/data/*  →  Firebase Admin SDK      ← reads
page (client)  →  lib/api/*   →  Python API              ← writes
```

Reads never go through the Python API. Writes never go straight to Firestore.
→ [ADR 0005](../../../.docs/adr/0005-reads-bypass-python.md) · [ADR 0007](../../../.docs/adr/0007-deny-all-client-writes.md)

`lib/data/` is the **only** place Firestore is queried. Components never import the SDK.

## Public pages — `src/app/(site)/`

Server Components by default. This is what makes the site SEO-viable — the whole reason the project
isn't Flutter. → [ADR 0001](../../../.docs/adr/0001-nextjs-instead-of-flutter-web.md)

```tsx
// Next 16: params and searchParams are Promises — always await them.
type Params = Promise<{ slug: string }>;

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { slug } = await params;
  const project = await getProjectBySlug(slug);
  if (!project) return {};
  return {
    title: project.seo?.metaTitle ?? project.title,
    description: project.seo?.metaDescription ?? project.summary,
    alternates: { canonical: `/projects/${project.slug}` },
    openGraph: { images: [project.seo?.ogImageUrl ?? project.cover?.url] },
  };
}

export default async function Page({ params }: { params: Params }) {
  const { slug } = await params;
  const project = await getProjectBySlug(slug);
  if (!project) notFound();
  return <ProjectDetailView project={project} />;
}
```

Every public page needs: `generateMetadata`, a canonical URL, `notFound()` on a missing document,
and JSON-LD where a schema.org type fits.

## Client Components

Push `"use client"` **as deep as possible**. A client `<ThemeToggle>` inside a server `<Nav>`, never
a client `<Nav>` — one misplaced directive pulls the entire subtree into the browser bundle.

Reach for a Client Component only for: event handlers, hooks, browser APIs, or Firebase Auth.

## Optional fields render conditionally

The models are a small required core plus many optional fields. Render a section **only** when its
data exists. → [ADR 0008](../../../.docs/adr/0008-projects-drop-start-end-dates.md)

```tsx
{project.content?.challenges?.length ? (
  <Section title="Challenges">…</Section>
) : null}
```

No empty headings, no `null` placeholders, no "coming soon". A project with three filled fields must
look intentional, not broken.

## Admin screens — `src/app/(admin)/admin/`

- Behind two gates: `src/proxy.ts` (session-cookie presence, cheap) and
  `(admin)/admin/(protected)/layout.tsx` (`verifySessionCookie` + the `admin` claim — the real check)
- Writes go through `lib/api/`, never Firestore directly
- Forms use `<SchemaForm>` with the generated Zod validators — adding a field to a schema should
  make it appear in the form with **no form code changes**
- Optimistic updates need a rollback path; a silent revert reads as a bug
- Nothing in `(site)/` or `components/site/` may import admin code — ESLint enforces this

## Non-negotiables

- **`import "server-only"`** at the top of any file touching the Admin SDK
- **Strip confidential data server-side** in `lib/data/`. Filtering in a component still ships the
  value in the RSC payload
- **`next/image` with correct `sizes`**, always. Dimensions are in the schema to prevent layout shift
- **Design tokens only** — no hard-coded hex values or arbitrary spacing
- **Fresh reads** — `(site)/` renders per request (`revalidate = 0`, ADR 0014). Don't add
  `unstable_cache` or `"use cache"` for content: nothing invalidates it any more (ADR 0015)

## Accessibility — not optional, CI enforces it

Semantic landmarks · keyboard navigable · visible focus rings · alt text on every image ·
AA contrast in both themes · `prefers-reduced-motion` honoured.

## Verify

```bash
make lint    # tsc --noEmit + eslint
make test
make dev     # check at 640 / 1024 / 1280
```

Then: `view-source` must show the actual content, not an empty shell. That's the SEO test, and it's
the reason for the whole architecture.
