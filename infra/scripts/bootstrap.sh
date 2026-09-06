#!/usr/bin/env bash
# One-time project bootstrap.
#
# Does everything that has a CLI, and prints a checklist for the console-only steps
# Terraform genuinely cannot perform. See docs/plan/04-infrastructure.md.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-nikunjramani-in}"
REGION="${REGION:-asia-south1}"
STATE_BUCKET="${PROJECT_ID}-tfstate"
ACCOUNT="${GCLOUD_ACCOUNT:-}"

gc() {
  if [ -n "$ACCOUNT" ]; then gcloud --account="$ACCOUNT" "$@"; else gcloud "$@"; fi
}

echo "▶ project: $PROJECT_ID   region: $REGION"
[ -n "$ACCOUNT" ] && echo "▶ account: $ACCOUNT"
echo

# ── 1 · project must exist and have billing ────────────────────────
if ! gc projects describe "$PROJECT_ID" >/dev/null 2>&1; then
  echo "✗ Project $PROJECT_ID not found, or this account cannot see it."
  echo "  Create it at https://console.firebase.google.com, then re-run."
  exit 1
fi
echo "✓ project exists"

BILLING=$(gc billing projects describe "$PROJECT_ID" --format="value(billingEnabled)" 2>/dev/null || echo "False")
if [ "$BILLING" != "True" ]; then
  cat <<'MSG'
✗ Billing is not enabled.

  Storage, Cloud Functions and App Hosting cannot be created without it — this is a
  platform requirement, not a choice in the plan. The expected bill is still zero:
  everything sits inside the free tier, and Terraform adds a budget alert plus
  per-function instance caps.

  Enable Blaze:  https://console.firebase.google.com/project/PROJECT/usage/details

MSG
  exit 1
fi
echo "✓ billing enabled"

# ── 2 · Terraform state bucket (chicken-and-egg: predates Terraform) ─
if gc storage buckets describe "gs://${STATE_BUCKET}" >/dev/null 2>&1; then
  echo "✓ state bucket exists"
else
  echo "▶ creating state bucket gs://${STATE_BUCKET}"
  gc storage buckets create "gs://${STATE_BUCKET}" \
    --project="$PROJECT_ID" --location="$REGION" --uniform-bucket-level-access
  gc storage buckets update "gs://${STATE_BUCKET}" --versioning
  echo "✓ state bucket created"
fi

# ── 3 · console-only steps ─────────────────────────────────────────
cat <<MSG

────────────────────────────────────────────────────────────────
These cannot be scripted. Do them once in the console:

  1. OAuth consent screen (External, your email as support contact)
     https://console.cloud.google.com/apis/credentials/consent?project=${PROJECT_ID}

  2. Enable the Google sign-in provider
     https://console.firebase.google.com/project/${PROJECT_ID}/authentication/providers

  3. Firestore: create the database in NATIVE mode, region ${REGION}
     ⚠ Datastore mode is irreversible — do not pick it.

Then:
     cd infra/terraform/envs/prod
     cp terraform.tfvars.example terraform.tfvars   # fill it in
     terraform init && terraform plan
────────────────────────────────────────────────────────────────
MSG
