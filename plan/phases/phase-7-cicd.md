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

- [ ] WIF pool + provider in Terraform, scoped to this repo
- [ ] Deploy service account with least privilege
- [ ] Repo-level bindings
- [ ] Verified: a workflow authenticates with **no** JSON key
- [ ] Any existing SA keys deleted

### 7.2 · PR checks

- [ ] `schemas.yml` — validate, `make gen`, fail on diff
- [ ] `ci-frontend.yml` — tsc, eslint, vitest, build, Lighthouse CI
- [ ] `ci-backend.yml` — ruff, mypy strict, pytest on the emulator
- [ ] `infra-plan.yml` — fmt, validate, plan posted as a PR comment
- [ ] Path filters so unrelated changes don't run everything
- [ ] Dependency caching (npm, uv)

### 7.3 · Preview deploys

- [ ] `preview.yml` — App Hosting preview channel per PR
- [ ] Preview URL commented on the PR
- [ ] Previews point at prod Firestore **read-only**, or a seeded emulator
- [ ] Channels cleaned up on merge

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
4. Every PR gets a working preview URL
5. Hand-editing a generated file turns CI red
6. A failed smoke test rolls back without you intervening

---

## Gotchas

**WIF setup is fiddly.** The attribute condition on the provider must match the repo exactly, or
auth fails with a message that doesn't say why. Get one workflow authenticating before writing the
other six.

**Preview deploys writing to prod data will hurt.** Read-only, or a separate seeded project.

**Lighthouse CI is flaky on shared runners.** Use a median of three runs and a slightly forgiving
threshold, or you'll be re-running builds for nothing.

**Emulator startup dominates backend CI.** Cache the emulator binaries or the suite takes minutes
for seconds of tests.

**Branch protection on a solo repo feels silly right up until it saves you.** Keep it.

---

**Next:** [Phase 8 · Post-Launch](./phase-8-post-launch.md)
