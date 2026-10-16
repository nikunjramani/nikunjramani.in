# 0021 · The public site and the admin are separate surfaces with their own root layouts

**Status:** ✅ Accepted · **Date:** 2026-10-16
**Deciders:** Owner

---

## Context

One Next.js app serves two very different audiences: visitors reading the portfolio, and one
owner editing it at `/admin`. Until now they shared one root layout, one stylesheet and one
`components/` tree split into `site/` and `admin/` subfolders, with admin-only helpers
(`lib/api`, `merge-patch`, the session cookie code) mixed into the shared `lib/`.

The public site is about to be redesigned (Phase 2's "Technical" direction) while the admin keeps
its current, utilitarian look. With a single stylesheet, every token a redesign touches changes
the admin too, and every utility class used anywhere ships to every visitor. A lint rule already
stopped site code importing admin code, but nothing in the folder layout said which code belonged
to which surface.

## Decision

Each surface is a top-level folder, and each route group is its own **root layout**:

```
src/
  app/(site)/layout.tsx    <html> for the public site → site/site.css
  app/(admin)/layout.tsx   <html> for the admin      → admin/admin.css
  app/global-not-found.tsx 404 for a URL matching neither (experimental.globalNotFound)
  site/     components/, lib/ (contact, App Check), site.css     — public only
  admin/    components/, api/, auth/, lib/ (merge-patch, format), admin.css — admin only
  shared/   components (theme provider, skip link, route error), fonts, styles/base.css
  lib/      shared non-UI code: data/ (Firestore reads), firebase/, site, utils, blurhash
```

Each stylesheet imports Tailwind with `source(none)` and lists its own `@source` folders, so a
surface's CSS holds only the classes its code uses. Both start from `shared/styles/base.css` and
override tokens on their own.

Dependencies point one way, enforced by `no-restricted-imports` in `eslint.config.mjs`: `site`
and `admin` may import `shared`, `lib` and `generated`; `shared` and `lib` import neither surface;
`site` never imports `admin`. The one sanctioned crossing is **admin → site components**: the
project editor previews with the real `ProjectDetailView` and `Markdown`, so the preview is the
page, not a lookalike.

## Consequences

### What this makes easier

- The site can be redesigned — tokens, fonts, layout — without touching the admin, and vice versa.
- Visitors download only site CSS (≈21 KB vs. the admin's ≈27 KB at the time of the split, from
  one shared bundle before). Admin-only code is now visibly admin-only by path.
- "Where does this go?" has an answer: one surface → that surface's folder; both → `shared`/`lib`.

### What this makes harder — the cost we're accepting

- Moving between `/admin` and the site is a **full page load** (Next's rule for crossing root
  layouts). It happens only when the owner clicks "view site", so it's acceptable.
- `global-not-found.tsx` is **experimental** in Next 16 and has to bring its own `<html>`,
  stylesheet and theme provider. If the flag changes behaviour in an upgrade, unmatched URLs are
  where it will show.
- `<html>`, fonts and `ThemeProvider` are repeated in three files (two layouts + global 404). Kept
  small by sharing `fontVariables`, `SkipLink` and `ThemeProvider` from `shared/`.
- The admin preview renders site components with **admin** tokens. Once the site's tokens diverge
  the preview is faithful in structure, not in colour and type, until the preview opts into site
  tokens.

## Alternatives considered

### Keep one root layout, scope tokens with `[data-surface]`
Lets the designs diverge, but every class still ships to both surfaces and the folder layout
still mixes admin helpers into shared code. Solves half the problem.

### A separate Next.js app for the admin
The cleanest isolation, but two App Hosting backends, two builds, cross-origin session cookies
and duplicated data/auth code — far too much machinery for one editor (ADR 0010 already declined
monorepo tooling).

### Move every `lib/` file under a surface
`lib/data` and `lib/firebase` are used by both surfaces (the media-usage route and the
session code read through them), so splitting them would mean duplicates or a third shared
folder anyway.

## Revisit if

- `global-not-found` is removed or changes semantics in a Next upgrade.
- The admin grows to need its own deploy cadence or a different domain — then a separate app.
- The full page load between surfaces starts to matter (e.g. an inline "edit this page" flow).
