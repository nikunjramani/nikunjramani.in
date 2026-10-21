---
name: ship
description: Get a change to production, roll back a bad deploy, approve an infra change, add or rotate a secret, or restore a backup. Use for anything deploy- or rollback-shaped — production deploys run in CI on merge to main, and the order of operations matters.
---

# Shipping

Production deploys are **CI's job**: merge to `main` → `deploy.yml`. Full flow:
[.docs/CODE_FLOW.md](../../../.docs/CODE_FLOW.md) (CI/CD). Operations detail:
[.docs/RUNBOOK.md](../../../.docs/RUNBOOK.md).

## The normal path

1. PR → `pr.yml` runs only the checks its paths touch, then deploys only the touched targets to
   **staging** and comments the URL. Check the preview.
2. CI green → merge (squash). Use the `pull-request` skill.
3. `deploy.yml` on `main`: `changes` → `deploy` (the API image to Cloud Run + its smoke test →
   rules → App Hosting, retried 3× → smoke test of `/` and `/api/v1/ops/health`) → `rollback` if
   that failed → `terraform` if `infra/terraform/**` changed (staging, then prod behind the
   owner's `production-infra` approval).
4. Watch the `deploy` run to the end and report the result. A failed `deploy` with a green
   `rollback` means prod is back on the previous commit — still a failure to fix.

## Order traps

- **The API binding a brand-new secret**: CI deploys code before Terraform, so the secret
  wouldn't exist yet. Run the workflow manually with `infra_only` first, have the owner add the
  value, then merge the code.
- **A new Firestore query**: its composite index ships in the same deploy (rules + indexes go
  first) but builds asynchronously — the query can fail for minutes after deploy.
- **A module adding a new GCP resource type**: the Terraform *apply* identity needs a role for it
  (`.claude/rules/infra.md`), granted by hand once in existing projects.

## Rollback

| Broken | Fix |
|---|---|
| A deploy (automatic) | the API: `cloud-run-deploy` puts traffic back on the previous revision; rules and site: `deploy.yml`'s `rollback` job redeploys the previous commit |
| The API, by hand | `gcloud run services update-traffic api --region asia-south1 --to-revisions <previous>=100` (revisions: `gcloud run revisions list --service api`) |
| Frontend | App Hosting console → previous release |
| Rules | revert PR → merge (CI redeploys rules) |
| Infra | revert PR → merge → approve the apply |
| Data | restore from the nightly export (below) |

**Roll back first, diagnose after.**

## Secrets

The owner adds values; the agent never writes to Secret Manager. Give them the exact command,
value piped, not on disk:

```bash
echo -n "value" | gcloud secrets versions add NAME --data-file=- --project=<project>
```

Rotation: add the new version → redeploy the API (`latest` is read at deploy) → verify the path that uses it → disable the
old version. Not-yet-configured secret: a single newline (empty versions are rejected).

## Backups

Nightly per-document JSON export into `<project>-backups` (30-day retention). Restore into the
**emulator** first and verify, always, before touching production.

## Smoke test by hand

Site over HTTPS · a project page renders · `view-source` shows real content · contact form stores
a message · `/admin` login works · an admin edit shows publicly at once · the `api` service's logs clean.
