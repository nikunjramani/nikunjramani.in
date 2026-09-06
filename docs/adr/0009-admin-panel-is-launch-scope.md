# 0009 · Admin panel is launch scope

**Status:** ✅ Accepted · **Date:** 2026-09-06

---

## Context

Originally the admin panel was deferred to post-launch, with content edited in the Firebase console
and via a seeding script in the meantime. The requirement was then stated explicitly: log in on the
site itself at a specific URL, and edit projects, skills and everything else from there.

The underlying concern is real and worth naming. A personal site's actual failure mode isn't bugs —
it's going stale. A site that needs a console visit or a deploy to update is a site that stops
getting updated, usually within about three months.

## Decision

The admin panel ships **at launch**, as Phase 5, before the deploy phase.

Fixed route list: dashboard, projects (with drag-reorder and a full editor), skills, experience,
education, certifications, profile, media library, messages inbox, settings. Google sign-in gated on
the `admin` custom claim.

## Consequences

### What this makes easier

- Content updates take minutes, from a phone if needed — so they actually happen
- No production Firebase console access needed for routine work
- Draft/preview/publish becomes a real workflow, so half-written projects can sit safely unpublished
- Media uploads with automatic image processing, rather than manual Storage juggling
- It's a genuinely demonstrable piece of engineering, which is on-theme for a portfolio

### What this makes harder — the cost we're accepting

- **~14 hours, pushing launch out by roughly a week**
- A whole authenticated application to build, secure and maintain
- The largest scope-creep risk in the project — an admin panel can absorb infinite effort
- More surface area to secure ([0007](./0007-deny-all-client-writes.md) is what keeps that bounded)

The scope risk is mitigated by the fixed route list above. Anything not on it goes to Phase 8. No
rich-text WYSIWYG, no revision history, no collaborative editing — markdown in a textarea with a
preview toggle.

The cost is also much lower than it looks, because [0006](./0006-json-schema-source-of-truth.md)
means the forms are generated from the schemas rather than hand-built.

## Alternatives considered

### Firebase console + seed script
Zero build cost. Rejected: raw document editing with no validation, no preview, no image handling,
and unpleasant enough that it wouldn't get used.

### A headless CMS (Sanity, Contentful)
Good editing experience, no build cost. Rejected: another vendor and another free tier to depend on,
content living outside our own database, and it makes [0006](./0006-json-schema-source-of-truth.md)
largely pointless.

### Git-based content (MDX in the repo)
Version controlled, no admin needed. Rejected: every typo fix becomes a commit and a deploy, and
it's unusable from a phone.

## Revisit if

- Phase 5 overruns badly — in which case ship a cut-down version covering only projects and profile,
  and move the rest to Phase 8
