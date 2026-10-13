# 0018 · A separate Firebase project for PR preview deploys

**Status:** 🟡 Proposed · **Date:** 2026-10-13
**Deciders:** Owner

---

## Context

Phase 7 commits to giving every PR a live, clickable preview URL ([05 · CI/CD](../plan/05-cicd.md),
[phase-7-cicd.md](../plan/phases/phase-7-cicd.md) §7.3), so UI and backend changes can be verified
before merge instead of trusted on faith. The question is which Firebase project that preview runs
in.

This repo has exactly one Firebase project, `nikunjramani-in`, holding the real Firestore content,
the real Auth users, and the twelve production Cloud Functions. Reads bypass Python entirely
([ADR 0005](./0005-reads-bypass-python.md)) — the public site reads Firestore directly, so
previewing content/UI changes against real data is inherently safe, it's read-only by
construction. Writes are a different story: **every mutation goes through the Python API**
([ADR 0007](./0007-deny-all-client-writes.md)), and a PR that redeploys those functions into the
same project redeploys over the live ones. An admin-panel write exercised during review — the exact
thing a preview exists to let you do — would land in the real Firestore, under the real domain's
service account, no different from editing production by hand.

`04 · Infrastructure`'s "Environments" section anticipated this from day one: the Terraform modules
are already environment-parameterised, `envs/staging/` was pencilled in as "same modules, cheaper
knobs," and the deliberate choice back then was to defer it until "the admin panel exists and you
want to test a schema migration against real-shaped data." That condition is now true — Phase 5
(admin panel) is built, and Phase 7 preview deploys are the forcing function.

## Decision

Stand up a second Firebase project, `nikunjramani-in-staging`, under the **same billing account**
as prod (same Firebase account/owner — projects are free to create; only usage is billed, and a
low-traffic solo preview environment costs close to nothing on Blaze).

`infra/terraform/envs/staging/` mirrors `envs/prod/` — the same modules
(`project`, `iam`, `firestore`, `storage`, `secrets`, `monitoring`, `functions`, `app-hosting`),
pointed at the staging project id, with cheaper knobs (smaller budget, `max_instances = 1`). It gets
its own Firestore, its own Auth user base, its own twelve Cloud Functions, its own App Hosting
backend. Nothing is shared with prod except the owner's billing account and GitHub repo.

Staging is a **single long-lived environment, not one per PR**. `preview.yml` deploys whichever
PR branch last pushed — the same per-domain-changed-functions logic `deploy.yml` already uses for
prod — to this one staging project, then comments the PR with the staging URL. The next PR to push
overwrites whatever was there. For a solo repo with effectively one PR in flight at a time, that's
the whole budget this needs; it is not meant to scale to concurrent reviewers.

## Consequences

### What this makes easier

- A PR can be fully exercised — frontend *and* backend, including admin writes — against a real
  deployed stack before merge, with zero risk to production content or functions.
- The preview path exercises the exact same deploy mechanics (`firebase deploy --only functions`,
  `--only apphosting`, the Terraform modules) that prod uses, so the deploy path itself gets
  continuous practice instead of only running for real at launch time and at the next incident.
- No new code path in the app: `FUNCTIONS_BASE_URL` ([next.config.ts](../../frontend/next.config.ts))
  is already an env var, so pointing a preview build at the staging project's functions needs no
  frontend code change — just a different build-time value.

### What this makes harder — the cost we're accepting

- **A second environment to keep in sync.** Every Terraform module change applies to two `envs/*`
  trees now, not one; drift between them is a real risk the plan has to call out explicitly.
- **A second set of secrets.** Turnstile and Resend need staging-safe values (Cloudflare publishes
  an always-passes Turnstile test site/secret key pair for exactly this; `CONTACT_EMAIL_TO` should
  point at the owner's own inbox) so the contact form in staging never sends real-looking mail.
- **A second Auth/admin setup.** Google sign-in has to be enabled again in staging's console, and
  `set_admin_claim.py` run again for the owner's email, or admin-panel preview testing can't log in.
- **Staging is not isolated per PR.** Two PRs pushing around the same time stomp each other's
  preview. Acceptable for a solo repo today; a real limitation if that stops being true.
- **Firestore needs its own seed data.** It must never be a copy of prod — no real contact
  submissions, no real client or employer names (this repo is public; see `CLAUDE.md`) — so staging
  starts near-empty and is seeded with placeholder fixtures, not production exports.

## Alternatives considered

### Option 1 — Frontend-only preview, backend untouched
An App Hosting preview channel per PR, reading real Firestore directly (safe — reads bypass Python)
but talking to whatever backend is currently live in prod. Cheapest, matches the original Phase 7
sketch, and backend correctness still comes from the emulator-backed pytest suite. Rejected as the
long-term answer because it can never show a backend change live before merge — exactly the
scenario this ADR exists to cover — though it remains the easy fallback if staging upkeep turns out
not to be worth it.

### Option 2 — Same project, isolated via a second named Firestore database
Firestore supports multiple named databases per project. A preview-only database plus a suffixed,
second set of Cloud Functions in the same project would avoid standing up new infra. Rejected: it
still shares the project's Cloud Functions quota, IAM, and budget with prod, needs its own
`FIRESTORE_DATABASE_ID`-style plumbing through `kernel/firebase.py`, and needs a cleanup job to
delete the suffixed functions on every PR close — more new surface area than a second project, for
less isolation.

## Revisit if

- Keeping two Terraform environments in sync becomes the dominant source of toil rather than the
  deploy-path practice it's meant to buy.
- Concurrent PRs become common enough that one shared staging slot actively blocks review — at that
  point, per-PR ephemeral environments (Terraform workspaces, or a project-per-PR pattern) are the
  next step, not a reason to abandon the separate-project approach itself.
