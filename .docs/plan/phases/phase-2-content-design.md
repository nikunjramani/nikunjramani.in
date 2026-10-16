# Phase 2 · Content & Design Direction

**~5 hours, mostly yours** · Status: 🟡 Design chosen and built (2026-10-16); copy is live through the admin

> **Goal:** Real copy written, and a visual direction chosen and encoded as design
> tokens — so Phase 4 builds against reality instead of Lorem ipsum.

**Run this in parallel with Phases 1 and 3.** It's mostly your writing time, and it's the single
most likely thing to stall the project.

---

## Prerequisites

- [ ] [06 · Content Checklist](../06-content-checklist.md) read
- [ ] An hour where you won't be interrupted

---

## Part A · Content — yours, ~4h

Fill `.docs/CONTENT.md`. Full detail in the [content checklist](../06-content-checklist.md).

- [ ] **Identity** (30m) — name, headline, tagline, location, socials, availability
- [ ] **About** (1h) — three paragraphs: what you do · how you got here · who you are outside work
- [ ] **Skills** (30m) — grouped, rated 1–5, honest
- [ ] **Experience** (1h) — three achievement bullets per role, with numbers
- [ ] **Projects, 3–6** (2h) — problem, approach, outcomes, stack, media, links
- [ ] **Assets** — résumé PDF, headshot, screenshots, favicon

> **Write badly first.** Get all of it down in one sitting without editing. Editing prose that
> exists is easy; editing a blank page is not.

---

## Part B · Design direction — ~1h together

### B.1 · Three directions

I'll build three static mockups of the homepage hero + a project card, and you pick one. Rough
sketches of where they'd differ:

| Direction | Feel | Suits you if |
|---|---|---|
| **Editorial** | Large serif headings, generous whitespace, restrained colour, content-forward | You want the writing to carry it |
| **Technical** | Monospace accents, dense information, terminal-ish, subtle grid | You want it to read as an engineer's site |
| **Bold** | Big type, saturated accent, strong motion, high contrast | You want to be remembered |

- [x] Three mockups built *(as layout sketches)*
- [x] One chosen *(mixing elements is fine)* — **Technical**, 2026-10-16

### B.2 · Design tokens

Once chosen, encode it — no ad-hoc values in components later.

- [x] Colour scale, dark-first, with a light theme
- [x] Single accent colour, contrast-checked against both themes
- [x] Type scale — fluid `clamp()`, 6 steps
- [x] Font choice, **self-hosted** and subset *(never a runtime Google Fonts fetch)*
- [x] 4pt spacing scale *(Tailwind's default)*
- [x] Radii, shadows, border tokens *(no shadows by design)*
- [x] Motion: durations, easings, and a `prefers-reduced-motion` path
- [x] Breakpoints: 640 / 1024 / 1280 *(Tailwind's defaults)*

### B.3 · Write it down

- [x] [`.docs/DESIGN.md`](../../DESIGN.md) — tokens, rules, dos and don'ts
- [x] Tokens implemented in `frontend/src/site/site.css` *(Tailwind v4 has no config file)*
- [ ] A `/styleguide` route rendering every token and component state

---

## Definition of done

1. `.docs/CONTENT.md` has real copy for identity, about, skills, experience and at least 3 projects
2. A direction is chosen and `docs/DESIGN.md` written
3. Tokens live in Tailwind config, and no component will need a hard-coded hex
4. `/styleguide` renders every token
5. Contrast passes WCAG AA in **both** themes

---

## Gotchas

**Don't design in the browser before the copy exists.** Layouts built around placeholder text break
the moment real text arrives — real headlines are longer, real project titles wrap.

**Accent colour contrast is the usual trap.** A colour that looks great on dark often fails AA on
light. Check both before committing, not after building forty components.

**Self-host the fonts.** `next/font` with local files gives zero layout shift and no third-party
request. A runtime Google Fonts fetch costs you a flash of unstyled text and a Lighthouse point.

**Perfectionism risk is highest here.** Pick a direction in an hour, not a week. The site is
editable without a deploy — you can refine it live.

---

**Next:** [Phase 3 · Backend](./phase-3-backend.md)
