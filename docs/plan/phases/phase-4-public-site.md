# Phase 4 · Public Site

**~16 hours** · Status: ⬜ Not started

> **Goal:** Every public page built, rendering your real content, fast and accessible,
> with SEO done properly — the thing Flutter couldn't give us.

---

## Prerequisites

- [ ] [Phase 1](./phase-1-schemas.md) done — TypeScript types generated
- [ ] [Phase 2](./phase-2-content-design.md) done — real copy and design tokens
- [ ] Content seeded into Firestore

---

## Tasks

### 4.1 · Data layer

- [ ] `lib/firebase/admin.ts` — Admin SDK, server-only, singleton
- [ ] `lib/data/` — one typed query module per collection
- [ ] ISR caching with tags per collection
- [ ] `app/api/revalidate/route.ts` — token-protected, called by the backend on publish
- [ ] `notFound()` on missing docs, so a bad slug 404s properly

### 4.2 · Shell

- [ ] Root layout: fonts, theme provider, analytics slot
- [ ] Nav — sticky, responsive, mobile drawer, active state
- [ ] Footer — socials, copyright, back to top
- [ ] Theme toggle, no flash on load
- [ ] Page transitions
- [ ] `not-found.tsx` and `error.tsx`

### 4.3 · Home

- [ ] Hero — name, headline, tagline, CTAs, availability badge
- [ ] About preview → full About
- [ ] Featured skills
- [ ] Featured projects (3)
- [ ] Experience snapshot
- [ ] Contact CTA

### 4.4 · Projects

- [x] `/projects` — responsive grid
- [x] Filters: kind, tech, status — URL state, so filtered views are shareable
- [x] Empty and loading states
- [x] `ProjectCard` — cover, title, summary, stack chips, timeline label

### 4.5 · Project detail — the important one

The [progressive disclosure](../02-data-model.md#progressive-disclosure) page. Each block renders
**only if the data exists** — no empty headings, ever.

- [x] Header — title, subtitle, timeline, status, links
- [x] Cover image with blurhash placeholder
- [x] Overview · Problem · Approach
- [x] Architecture — description, diagram, component list
- [x] Challenges
- [x] **Outcomes** — before/after metrics, visually prominent
- [x] Learnings · Future work
- [x] Stack, grouped by category
- [x] Gallery with a lightbox
- [x] Testimonial · Awards · Collaborators
- [x] `client.confidential` → name stripped **server-side**, not hidden with CSS
- [x] Prev/next navigation

### 4.6 · Remaining pages

- [x] `/about` — full bio, skill matrix, education, certifications, résumé download
- [x] `/experience` — timeline, achievements, tech per role
- [x] `/contact` — form (react-hook-form + generated Zod), Turnstile, honeypot, success/error states

### 4.7 · SEO

- [x] `generateMetadata` per route — title, description, canonical, OG, Twitter
- [x] JSON-LD: `Person`, `WebSite`, `BreadcrumbList`, `CreativeWork` per project
- [x] `app/sitemap.ts` — generated from Firestore
- [x] `app/robots.ts`
- [x] `opengraph-image.tsx` — dynamic OG images per project
- [x] Canonical host consistent with the [redirect policy](../07-domain-setup.md#redirect-policy)

### 4.8 · Quality

- [x] Responsive at 640 / 1024 / 1280 — every page
- [x] Keyboard navigable, visible focus rings, skip-to-content link
- [x] Semantic landmarks, alt text everywhere, AA contrast
- [x] `prefers-reduced-motion` honoured
- [x] `next/image` everywhere, correct `sizes`
- [ ] Lighthouse ≥ 95 performance, 100 a11y, 100 SEO — **blocked**: "Localhost Lighthouse
      scores lie. Only production numbers count" (this doc's own gotcha), and Phase 6
      (deploy) is blocked on Blaze billing. Everything Lighthouse would check by static
      analysis — landmarks, alt text, contrast tokens, `next/image` sizes, canonical/OG/
      JSON-LD completeness — was verified by other means in this pass; only the actual
      score needs a live deploy.

---

## Definition of done

1. Every public route renders real Firestore content
2. A project with 3 filled fields looks intentional; one with 20 reads as a case study
3. Lighthouse: performance ≥ 95, accessibility 100, SEO 100
4. `view-source` shows the actual content — the SEO fix, demonstrated
5. Full keyboard navigation with visible focus
6. OG previews render correctly in LinkedIn and WhatsApp debuggers
7. Confidential client names appear nowhere in the HTML payload

---

## Gotchas

**`"use client"` creeps upward.** One interactive component near the top of the tree pulls
everything below it into the client bundle. Push it as deep as possible — a client `<ThemeToggle>`
inside a server `<Nav>`, not a client `<Nav>`.

**The Admin SDK must never reach the client.** Keep it in `lib/firebase/admin.ts` with
`import "server-only"` at the top. Without that guard the failure is a leaked credential, not a
build error.

**ISR needs revalidation wired up**, or edits won't appear until the cache expires. That's what the
backend's `on_content_published` trigger is for — test the whole loop.

**Dynamic OG images are slow to generate** and easy to get wrong. Build one, verify it in the
LinkedIn Post Inspector, then do the rest.

**Confidential clients must be stripped server-side.** Filtering in a component still ships the name
in the RSC payload. Strip it in `lib/data/`.

**Layout shift from images** — always pass width/height or `fill` with a sized container. The
schema stores dimensions for exactly this reason.

---

**Next:** [Phase 5 · Admin Panel](./phase-5-admin-panel.md)
