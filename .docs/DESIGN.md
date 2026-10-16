# Design — the public site

The site's visual system: what it is, where it lives, and the rules that keep it coherent. The
admin panel has its own, plainer look and is not covered here
([ADR 0021](./adr/0021-site-and-admin-are-separate-surfaces.md)).

**Direction:** *Technical*, chosen by the owner on 2026-10-16 from the three in
[Phase 2](./plan/phases/phase-2-content-design.md). The site reads as an engineer's **spec
sheet**: facts in ruled key/value tables, sections as labelled rows, one signal colour.

## Where it lives

| What | File |
|---|---|
| Colour, radius and type tokens | [frontend/src/site/site.css](../frontend/src/site/site.css) (on top of [shared/styles/base.css](../frontend/src/shared/styles/base.css)) |
| Fonts | [frontend/src/site/fonts.ts](../frontend/src/site/fonts.ts) |
| Structural components | [frontend/src/site/components/spec.tsx](../frontend/src/site/components/spec.tsx) — `SpecTable`, `SpecSection`, `Container`, `PageHeader` |
| Buttons and chips | [frontend/src/site/components/styles.ts](../frontend/src/site/components/styles.ts) |

## Colour

Dark is the default; both themes pass WCAG AA (ratios in the `site.css` header comment).

| Token | Dark | Light | Use |
|---|---|---|---|
| `background` | `#0c1b2a` ink | `#f4f7fa` paper | page |
| `surface` | `#112437` panel | `#ffffff` | inputs, image plates |
| `foreground` | `#e4ecf4` chalk | `#0c1b2a` ink | text |
| `muted-foreground` | `#8da2b8` slate | `#4a5f74` | secondary text, spec keys |
| `border` | `#22384f` | `#d3dde7` | every rule and outline |
| `accent` | `#f2b33d` signal | `#9a5b00` | primary button, current nav item, bullets, highlights |
| `danger` | `#f28b82` | `#b42318` | form errors only |

**One signal colour.** Amber marks what's current, primary or measured — never decoration.
Components use tokens only (`bg-accent`, `text-muted-foreground`); a hex value in a component is
a bug.

## Type

- **Archivo** (variable weight *and* width) for everything readable. Headings stretch wide —
  `font-stretch-125%` for page titles, `font-stretch-112%` for section and item titles — at
  `font-semibold` with tight tracking. Body text stays at normal width.
- **IBM Plex Mono** for data: spec keys, dates, figures, nav, chips, filter options. Never for
  sentences.
- Sizes come from the fluid scale in `base.css` plus `text-display` (the home page name only).
- Sentence case everywhere. No all-caps labels, no letter-spaced eyebrows.
- Prose is capped at `max-w-[68ch]`.

## Structure

- **`SpecSection`** — every page section is one spec row: a mono label in an 11rem left column
  on wide screens, stacked above the content on phones, with a rule on top.
- **`SpecTable`** — key/value facts in a ruled table (the hero's title block, a project's
  status/role/team, contact details). Rows with no value are dropped, so optional fields never
  leave an empty key (ADR 0008).
- **Lists are ruled rows, not cards.** Projects on the home page, roles, education and
  certifications are rows divided by `border-border` rules. The `/projects` index is the one grid,
  because covers matter there.
- Bullets are small amber squares (`list-[square] marker:text-accent`). No `·` separators —
  separate facts structurally (a spec row, a comma list) instead.
- Corners are nearly square: `rounded-(--radius)` (4px) on everything that has one.
- Layout is left-aligned in a `max-w-6xl` column with a 16px gutter on phones.

## Motion

One orchestrated moment: on the home page, the title block's rules draw in left to right on
load (`.draw-rule`, 90ms stagger). Everything else is a colour or underline change on hover or
focus. `prefers-reduced-motion` collapses all of it (`base.css`).

## Texture

A 24px blueprint grid (`.blueprint-grid`) sits behind the home hero only, faded out at the bottom.
It's the one decorative element; don't repeat it elsewhere.

## Copy

Plain, specific, sentence case. Buttons say what happens ("View projects", "Send message").
Empty and error states say what to do next ("Nothing matches these filters. Clear one to see
more.") rather than apologising. Never invent facts about the owner in UI copy — anything about
them comes from Firestore.

## Known gaps

- The admin's project preview renders these components with **admin** tokens and fonts, so it
  matches the page's structure but not its colours and type (FE-22).
- No `/styleguide` route yet (Phase 2 B.3).
- Light theme has been contrast-checked numerically, not reviewed in a browser by the owner.
