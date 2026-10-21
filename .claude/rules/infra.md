---
paths:
  - "infra/**"
---

# Infrastructure rules (Terraform, Firestore rules)

Decisions: `.docs/decisions/infra.md`; layout and what Terraform can't do:
`.docs/plan/04-infrastructure.md`; operations: `.docs/RUNBOOK.md`.

## Terraform

- **Two roots, one set of modules**: `infra/terraform/envs/{prod,staging}` → `modules/*`. A module
  change applies to both; staging applies first in CI (ADR 0018, 0019).
- **CI applies Terraform**, after the code deploy, staging then prod behind the
  `production-infra` approval. Locally you only `plan`.
- **When a module adds a resource type, give the *apply* identity the role to manage it**
  (`terraform_roles` in `modules/iam`). Terraform grants it in the same apply — the module must
  `depends_on = [module.iam]` so the binding lands first. A **manual grant is needed only when
  Terraform must refresh an existing resource it can't read** (it 403s before it can grant
  anything; lessons-learned 2026-10-16), **or when a PR preview needs the role before merge**:
  staging's Terraform applies only from `main`, so a role the *deploy* identity needs for the
  preview can't come from that PR's own apply.
- **Firebase resources need `google-beta`.** A 404 on the standard provider usually means this.
- **The `api` Cloud Run service is CI's, not Terraform's** (`make deploy-api`, ADR 0023), so a
  PR preview can create it in staging. Terraform (`modules/api`) owns what points at it — the
  Eventarc triggers and the scheduler job — which need it to exist: code deploys first.
- **Secrets**: Terraform creates the container only; values are added out-of-band, so none ever
  sits in state. Secret Manager rejects an empty version — a placeholder is a single newline.
- **Never commit** `*.tfvars` (only `*.tfvars.example`), `*.tfplan` or state — all gitignored, as
  is `.terraform.lock.hcl`. Billing account and alert email reach CI as GitHub secrets.
- `terraform fmt -recursive` before committing; CI checks it.
- **Look provider/module versions up live** before changing a constraint.

## Firestore rules

- The public-read block of `infra/rules/firestore.rules` is **generated** from the schemas
  (`architecture/codegen/gen-rules.py`); hand-edit only outside the generated markers.
- Clients write nothing, admin included; any collection not listed is denied by fallthrough.
- `infra/rules/tests/` (`npm test` there) checks the rules against the emulator. **CI doesn't run
  it** — run it locally after any rules change.
- **`infra/rules/storage.rules` is emulator-only.** The media bucket is plain GCS behind IAM, not a
  Firebase Storage bucket; `firebase deploy --only storage` fails on prod. Never deploy it.
