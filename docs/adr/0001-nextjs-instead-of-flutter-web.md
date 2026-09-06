# 0001 · Next.js instead of Flutter Web

**Status:** ✅ Accepted · **Date:** 2026-09-06

---

## Context

The site's primary job is to be found. Someone hears a name, searches it, and lands here — so
organic discoverability isn't a nice-to-have, it's the product requirement.

The original plan was Flutter Web, chosen because of existing Dart familiarity. On investigation
that turns out to be disqualifying:

- Flutter 3.47 renders through CanvasKit to a `<canvas>` element. The HTML renderer was removed.
- A crawler that doesn't execute JavaScript sees a page with effectively no content.
- Google *can* render JS, but on a delayed second pass and inconsistently.
- Link-preview bots — LinkedIn, WhatsApp, Slack, iMessage — don't render JS at all. Every shared
  link would be a bare URL with no title, description or image.
- Initial bundle is 1.5–2.5 MB before first paint.

Mitigations exist (JSON-LD in the head, a static HTML skeleton under the canvas, server-rendered
mirror pages) but they amount to maintaining a shadow copy of the site in a second technology
purely for crawlers.

## Decision

Build the frontend with **Next.js 16 (App Router) and TypeScript**. Public pages are React Server
Components that read Firestore server-side and emit fully-formed HTML.

## Consequences

### What this makes easier

- SEO stops being a problem to work around and becomes the default behaviour
- Link previews work without any extra machinery
- Faster first paint; no framework runtime needed before content is visible
- Firebase App Hosting has first-class Next.js support, so we stay inside one platform
- React + TypeScript is the most transferable skill available in this space
- Route groups give a clean split between the public bundle and the admin bundle

### What this makes harder — the cost we're accepting

- **A real learning curve.** React, TypeScript, Server vs Client Components and the App Router
  are all new. Phases are deliberately ordered so the simpler public site comes before the admin
  panel.
- The Server/Client Component boundary is genuinely subtle and easy to get wrong
- The JS ecosystem moves fast; more dependency churn than Dart
- Existing Dart knowledge doesn't transfer

## Alternatives considered

### Flutter Web
Rejected on SEO, as above. The mitigations are real but amount to building the content twice.

### Astro
Excellent for static content and would have produced the fastest possible public site. Rejected
because [0009](./0009-admin-panel-is-launch-scope.md) puts an authenticated, interactive admin
application in launch scope. Astro can do that with an island, but at that point Next.js is the
better-fitting tool for the whole job rather than the better tool for half of it.

### Static HTML + a template engine
Would satisfy SEO perfectly and be the least code. Rejected because content would live in the
repo, so every typo fix becomes a deploy — the opposite of what
[0009](./0009-admin-panel-is-launch-scope.md) requires.

## Revisit if

- The learning curve stalls progress for more than two weeks
- The admin panel gets cut from scope, which would make Astro clearly better
