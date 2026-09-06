# 0008 · Projects drop start/end dates

**Status:** ✅ Accepted · **Date:** 2026-09-06

---

## Context

The first data model gave projects `startDate` and `endDate`, copied from the experience model.
This was flagged as not making sense, and on reflection it doesn't.

Jobs have real boundaries — a start date, an end date, a payroll record. Projects don't:

- "A weekend in 2023"
- "On and off through 2024–25"
- "Started in college, still maintained"
- "Two weeks, but I don't remember which two"

Forcing these into a date range produces either false precision or empty fields. And the rendered
output — "01 Jan 2025 – 30 Apr 2025" — is worse than what you'd actually write by hand.

The first model was also far too thin to tell a project's story: title, summary, description,
stack, links. That's a list of things, not a portfolio.

## Decision

Replace the date pair with a **flexible timeline object**, and expand the model substantially with
**mostly-optional fields that render only when filled**.

```jsonc
"timeline": {
  "displayLabel": "2025 · 4 months",   // free text; what actually renders
  "year": 2025,                         // for sorting and filtering only
  "durationMonths": 4,
  "ongoing": false
}
```

Six required fields — `slug`, `title`, `summary`, `kind`, `status`, `visibility`. Everything else
optional: problem, approach, architecture, challenges, before/after outcome metrics, learnings,
future work, testimonial, awards, collaborators, gallery, video.

**Experience keeps real start and end dates**, because a job genuinely has them.

## Consequences

### What this makes easier

- The timeline renders exactly as written, for every kind of project
- A project with three fields looks intentional; one with twenty reads as a case study — no empty
  headings either way
- Before/after outcome metrics give projects the thing recruiters actually look for
- `client.confidential` allows employer work to be shown without naming the client
- `links` as an array means new link types need no schema change

### What this makes harder — the cost we're accepting

- Free-text labels can't be validated or sorted; `year` exists alongside purely for that
- Inconsistent labels across projects if written carelessly
- A large optional surface risks an intimidating admin form — mitigated by collapsing optional
  sections behind an "add a section" affordance
- Every optional block needs a conditional render, and each needs testing both ways

## Alternatives considered

### Keep dates, make them optional
Doesn't fix it. "2024–25" still can't be expressed, and an optional date is a field you feel
vaguely guilty about leaving blank.

### Free-text only, no structured fields
Simplest. Rejected: sorting projects chronologically and filtering by year are both genuinely
wanted.

### Keep the model thin, put detail in one markdown blob
Easier to author. Rejected: the site can't then render outcome metrics distinctly, build filters, or
lay out sections differently — everything becomes a wall of prose.

## Revisit if

- Free-text labels turn out inconsistent enough to look sloppy in the grid
