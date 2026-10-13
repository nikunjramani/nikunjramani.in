# Phase 7 · CI/CD Hardening

**~5 hours** · Status: ⬜ Not started

> **Goal:** Push to `main` deploys safely; every PR is checked automatically; no
> long-lived credentials anywhere.

Done **after** launch on purpose — the deploy path is proven manually first, so when you
automate it you're encoding something known to work.

---

## Prerequisites

- [ ] [Phase 6](./phase-6-deploy.md) done — deployed manually at least once
- [ ] [05 · CI/CD](../05-cicd.md) read

---

## Tasks

### 7.1 · Workload Identity Federation

- [ ] WIF pool + provider in Terraform, scoped to this repo — **one per environment**: the
      `iam` module creates its own pool, provider and `github-deploy` SA inside whichever
      project it's applied to, so `envs/prod/` and `envs/staging/` ([§7.3](#73--staging-project--preview-deploys--adr-0018))
      each get a fully separate, least-privilege identity — never one shared across both
- [ ] Deploy service account with least privilege (×2 — prod and staging)
- [ ] Repo-level bindings
- [ ] A GitHub **environment** per target (`production`, `staging`) holding that env's
      `WIF_PROVIDER` / `DEPLOY_SA` vars, so a workflow step can't point at the wrong project
- [ ] Verified: a workflow authenticates with **no** JSON key, for both environments
- [ ] Any existing SA keys deleted

### 7.2 · PR checks

- [ ] `schemas.yml` — validate, `make gen`, fail on diff
- [ ] `ci-frontend.yml` — tsc, eslint, vitest, build, Lighthouse CI
- [ ] `ci-backend.yml` — ruff, mypy strict, pytest on the emulator
- [ ] `infra-plan.yml` — fmt, validate, plan posted as a PR comment
- [ ] Path filters so unrelated changes don't run everything
- [ ] Dependency caching (npm, uv)

### 7.3 · Staging project & preview deploys — [ADR 0018](../../adr/0018-staging-project-for-pr-previews.md)

Resolved: previews run against a **second, separate Firebase project**
(`nikunjramani-in-staging`, same billing account), not the same project prod runs in — a PR
redeploying functions must never be able to overwrite live data or live functions. It's one
long-lived shared environment, not one per PR; the most recently pushed PR is whatever's live
there.

**Bootstrap (one-time, manual — same category as Phase 0's `bootstrap.sh` steps):**

- [ ] Create the `nikunjramani-in-staging` GCP project, attach the same billing account
- [ ] `firebase projects:addfirebase` for the new project
- [ ] Enable the Google Auth provider in the staging project's console (no Terraform equivalent)

**Terraform:**

- [ ] `infra/terraform/envs/staging/` — copy `envs/prod/`, same modules
      (`project`, `iam`, `firestore`, `storage`, `secrets`, `monitoring`, `functions`,
      `app-hosting`), staging project id, cheaper knobs (`budget_amount` small, `max_instances = 1`)
- [ ] New state prefix (`envs/staging` in the existing `nikunjramani-in-tfstate` bucket, or a
      dedicated staging bucket — decide and record the choice in [04 · Infrastructure](../04-infrastructure.md))
- [ ] `terraform apply` against staging — same two-apply dance as prod for `functions_deployed`
      (false until the first functions deploy, then flipped true)

**Secrets (staging-safe values, never prod values):**

- [ ] `TURNSTILE_SECRET_KEY` — Cloudflare's published always-passes test key pair, not the real one
- [ ] `RESEND_API_KEY` / `CONTACT_EMAIL_TO` — the owner's own inbox, so staging mail is
      identifiable as staging mail, never a real client/employer address

**First deploy & admin access:**

- [ ] `firebase deploy --only firestore:rules,firestore:indexes,storage` against staging
- [ ] `firebase deploy --only functions` against staging (seeds the Cloud Run services the IAM
      invoker binding needs)
- [ ] `python infra/scripts/set_admin_claim.py <owner email>` against the staging project
- [ ] Seed staging Firestore with placeholder fixtures — never a prod export, never real contact
      submissions or real client/employer names (this repo is public)

**CI:**

- [ ] `preview.yml` — on every PR push: resolve the changed function domains (same path-filter
      logic `deploy.yml` uses), deploy those domains + App Hosting to the **staging** project
- [ ] Gated on the §7.2 check jobs passing (`needs:` in the workflow) — staging never ends up
      running code that fails lint, type-check or tests either
- [ ] Preview URL commented on the PR, explicitly labelled staging (so it's never mistaken for prod)
- [ ] Authenticates with staging's own WIF provider/SA from §7.1 — never the prod one
- [ ] Optional: `staging.nikunjramani.in` DNS, `noindex`d so it's never crawled

**Not needed:** channel cleanup on merge — there's one shared slot, not one per PR, so there's
nothing to tear down between PRs.

### 7.4 · Production deploy

- [ ] `deploy.yml` on push to `main`
- [ ] Order: terraform apply → rules → functions → App Hosting
- [ ] GitHub `production` environment with a required reviewer on `terraform apply`
- [ ] Post-deploy smoke test hitting `/health` and the homepage
- [ ] Auto-rollback if the smoke test fails

### 7.5 · Branch protection

- [ ] `main` protected — no direct pushes
- [ ] Required checks: schemas, frontend, backend, infra
- [ ] Squash merge, linear history
- [ ] Conversation resolution required

### 7.6 · Monitoring & maintenance

- [ ] `backup-verify.yml` nightly
- [ ] Dependabot or Renovate for npm, pip and Actions
- [ ] Uptime alerts routed to email
- [ ] Error-rate alert verified by deliberately triggering it

---

## Definition of done

1. A PR runs only the relevant checks, and merging is blocked until they're green
2. Merging to `main` deploys automatically, with an approval gate on infra changes
3. No service-account JSON key exists anywhere
4. Every PR gets a working preview URL, deployed to the staging project ([ADR 0018](../../adr/0018-staging-project-for-pr-previews.md)) — never the production one
5. Hand-editing a generated file turns CI red
6. A failed smoke test rolls back without you intervening

---

## Gotchas

**WIF setup is fiddly.** The attribute condition on the provider must match the repo exactly, or
auth fails with a message that doesn't say why. Get one workflow authenticating before writing the
other six.

**Previews run in a second Firebase project, not prod ([ADR 0018](../../adr/0018-staging-project-for-pr-previews.md)).** A PR that redeploys functions into the same project prod runs in redeploys over the live ones — the exact risk this ADR exists to avoid.

**Staging is one shared slot, not one per PR.** The most recently pushed PR is whatever's live there. Two PRs pushing around the same time stomp each other's preview — fine for a solo repo, a real limit if that changes.

**Terraform drift between `envs/prod/` and `envs/staging/` is a new failure mode.** A module change now has to be reviewed against both environments, not one.

**Lighthouse CI is flaky on shared runners.** Use a median of three runs and a slightly forgiving
threshold, or you'll be re-running builds for nothing.

**Emulator startup dominates backend CI.** Cache the emulator binaries or the suite takes minutes
for seconds of tests.

**Branch protection on a solo repo feels silly right up until it saves you.** Keep it.

---

**Next:** [Phase 8 · Post-Launch](./phase-8-post-launch.md)
