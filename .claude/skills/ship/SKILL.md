---
name: ship
description: Deploy this project to production, or roll back a bad deploy. Use for any deploy, rollback, secret rotation, or backup restore — the order of operations matters and getting it wrong takes the site down.
---

# Shipping

## Order matters

Dependencies run one way. This sequence is not optional:

```
1. terraform apply        infra, IAM, secrets, indexes
2. firebase deploy        rules + indexes
3. firebase deploy        functions      ← needs secrets to exist
4. App Hosting            auto-builds from the git push
5. smoke test
```

```bash
make deploy    # runs 1–3 in order
```

## Pre-flight

- [ ] `make lint` and `make test` green
- [ ] `make gen && git diff --exit-code` clean — no stale generated code
- [ ] `terraform plan` reviewed; nothing unexpected being destroyed
- [ ] New secrets present in Secret Manager
- [ ] New Firestore indexes deployed **before** the code that queries them
- [ ] Not a Friday evening

## Smoke test — every time

- [ ] `https://nikunjramani.in` loads over HTTPS
- [ ] A project detail page renders fully
- [ ] `view-source` shows real content, not an empty shell
- [ ] Contact form delivers an email
- [ ] `/admin` login works
- [ ] An admin edit appears on the public site within seconds
- [ ] Function logs clean — check immediately, this is where missing secrets surface

## Rollback

| Broken | Fix |
|---|---|
| Functions | `firebase functions:rollback` |
| Frontend | App Hosting console → previous release |
| Rules | `git revert`, then `firebase deploy --only firestore:rules` |
| Infra | `git revert`, then `terraform apply` |
| Data | Restore from the nightly Storage export |

**Roll back first, diagnose after.** A reverted deploy costs minutes; a debugging session on a live
broken site costs an afternoon.

## Secret rotation

1. Add the new version in Secret Manager
2. Redeploy functions so they pick it up
3. Verify the dependent path works (send a test email, submit a contact form)
4. Disable the old version — don't delete it until the new one is proven

## Restoring a backup

Exports land nightly in Storage, retained 30 days. Restore into the **emulator** first and verify
before touching production, always.

## Gotchas

- **Secrets are runtime-only, not deploy-time.** Reading one at module import fails the deploy with
  an unhelpful error.
- **Indexes before queries.** Deploy the index, wait for it to build, then deploy the code.
- **Localhost Lighthouse scores lie.** Only production numbers count.
- **Check DNS with `dig`, not a browser.** Browsers and ISPs cache aggressively.
- **`/docs` must be disabled in production.**

Full detail: [Phase 6](../../../docs/plan/phases/phase-6-deploy.md) · `docs/RUNBOOK.md`
