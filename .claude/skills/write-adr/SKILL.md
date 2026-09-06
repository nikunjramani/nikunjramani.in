---
name: write-adr
description: Record an architecture decision in docs/adr/. Use whenever an architectural choice is made or changed — framework, data model shape, security posture, deployment topology, or anything a future reader would question.
---

# Writing an ADR

## When

✅ Framework, language or datastore choice · data model shape · security posture · auth model ·
deployment topology · anything you'd have to justify in a code review

❌ Variable naming · colour choices · an obvious dependency · anything trivially reversible

The test: would a stranger — including this project's author, next year — ask *"why on earth is it
like this?"*

## Steps

**1 · Next number.** `ls docs/adr/` and take the next in sequence. Never reuse or renumber.

**2 · Copy the template.**

```bash
cp docs/adr/TEMPLATE.md docs/adr/0011-short-kebab-title.md
```

Title states the decision, not the topic: `0011-cache-projects-in-redis`, not `0011-caching`.

**3 · Write it.** Sections in order of importance:

- **Context** — the situation forcing a decision, and the real constraints. Write for someone who
  knows nothing about the project. This is the section that ages best.
- **Decision** — what we're doing. Present tense, plainly. Usually the shortest section.
- **Consequences** — split into what gets easier and **what gets harder**. The cost section is
  mandatory. An ADR with no downside listed hasn't been thought through.
- **Alternatives considered** — what was rejected and why. Six months on, "why not X?" is the
  question actually being asked.
- **Revisit if** — the conditions that would reopen this. Turns a historical note into something
  actionable.

**4 · Add the index row** in `docs/adr/README.md`, with status and date.

**5 · Commit it with the change it describes.** Same PR, not a follow-up.

## Superseding

**ADRs are immutable.** Never edit an accepted one because the decision changed.

1. Write the new ADR; reference the old one in its Context
2. Change the old one's status to **Superseded by** with a link to the new one — and change nothing else
3. Update both index rows

The record of what was believed at the time *is* the value. Rewriting history destroys it.

## Tone

Plain and specific. Name the real constraint — a learning curve, a free tier, a stale docs page.
Vague ADRs ("for better maintainability") are worthless; the honest ones ("this costs a week and a
real learning curve, accepted because SEO is the product requirement") are what future readers need.

See [ADR 0001](../../../docs/adr/0001-nextjs-instead-of-flutter-web.md) for the shape.
