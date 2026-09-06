# 04 · Infrastructure

Everything reproducible lives in Terraform. The handful of things that can't are listed
honestly rather than pretended away.

---

## Layout

```
infra/
├── terraform/
│   ├── modules/
│   │   ├── project/       # APIs enabled, labels, budget alert
│   │   ├── firestore/     # database, indexes, rules release, TTL policies
│   │   ├── storage/       # buckets, rules, CORS, lifecycle
│   │   ├── functions/     # 2nd-gen functions, runtime SA, min/max instances
│   │   ├── app-hosting/   # Next.js backend, GitHub link, env vars
│   │   ├── iam/           # least-privilege SAs + WIF pool for GitHub
│   │   ├── secrets/       # Secret Manager entries + accessor bindings
│   │   └── monitoring/    # budget alert, uptime check, error-rate alert
│   ├── envs/
│   │   ├── prod/          # nikunjramani-in
│   │   └── staging/       # optional; same modules, cheaper knobs
│   └── backend.tf         # GCS remote state + locking
├── rules/
│   ├── firestore.rules
│   ├── firestore.indexes.json
│   └── storage.rules
└── scripts/
    ├── bootstrap.sh       # the manual steps, scripted where possible
    └── set_admin_claim.py
```

Providers: `google` **and** `google-beta`. Firebase resources live in the beta provider — that's
normal and expected, not a workaround.

---

## What Terraform can't do

Being straight about this now saves an hour of confusion in Phase 0. These are **one-time, ~20
minutes**, and `bootstrap.sh` scripts the parts that have a CLI:

| Step | Why it's manual | Scriptable? |
|---|---|---|
| Create the GCP project + attach billing | Needs an account-level identity Terraform doesn't have yet | ✅ `gcloud` |
| Add Firebase to the project | Firebase-specific provisioning step | ✅ `firebase projects:addfirebase` |
| Create the Terraform state bucket | Chicken-and-egg: state has to live somewhere before state exists | ✅ `gsutil` |
| OAuth consent screen | Console-only | ❌ |
| Enable the Google auth provider | Console-only | ❌ |
| Authorise the GitHub connection for App Hosting | OAuth handshake needs a human | ❌ |

Everything after that is `terraform apply`, reviewable as a plan diff in a PR.

---

## Guardrails Terraform enforces

These exist so a mistake costs nothing:

| Guardrail | Value | Why |
|---|---|---|
| Function `max_instances` | 3 | A runaway loop can't scale into a bill |
| Function `min_instances` | 0 | Scale to zero; cold start is fine on the write path |
| Budget alert | ₹500, notify at 50/90/100% | Early warning, not a surprise invoice |
| Storage lifecycle | Backups deleted after 30 days | Bounded growth |
| Uptime check | `/health` every 5 min | You hear about an outage before a visitor does |
| Log-based alert | Error rate > 5/min | Catches a bad deploy |
| Firestore TTL | `contact_messages` after 2 years | Data minimisation |

---

## State

Remote state in a GCS bucket with versioning and object locking. Locking matters even in a
one-person project — it's what stops a local `apply` and a CI `apply` from racing and corrupting
state.

```hcl
terraform {
  backend "gcs" {
    bucket = "nikunjramani-in-tfstate"
    prefix = "envs/prod"
  }
}
```

The bucket is created by `bootstrap.sh` and then left alone. Never in git: `*.tfstate`, `*.tfvars`.

---

## Environments

Starting **prod-only**. The modules are written to be environment-parameterised from day one, so
adding staging later is a new `envs/staging/main.tf` and a day's work — not a refactor.

A staging Firebase project is genuinely useful once the admin panel exists and you want to test a
schema migration against real-shaped data. Until then it's a second thing to keep in sync for no
benefit.

---

## Deploy order

Dependencies run in one direction, so this order is not optional:

```
1. bootstrap.sh          project, billing, Firebase, state bucket
2. terraform apply       APIs, IAM, Firestore, Storage, secrets, monitoring
3. firebase deploy       rules + indexes
4. firebase deploy       functions  (needs secrets to exist)
5. App Hosting           auto-builds from the git push
6. DNS                   see 07 · Domain Setup
```

Rollback: `firebase functions:rollback` for the API, App Hosting keeps previous releases one click
away, and Terraform state is versioned in the bucket.

---

**Next:** [05 · CI/CD](./05-cicd.md)
