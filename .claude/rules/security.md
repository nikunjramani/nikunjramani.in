# Security — public repository

Loaded every session.

- **The repository is public.** Never commit secrets, credentials, tokens, personal contact
  details, employer names, client names, or anything from a private engagement. Use a placeholder
  and say so. Git history has already had to be rewritten once — don't make it twice.
- **Secrets live in Secret Manager**, created as empty containers by Terraform
  (`infra/terraform/modules/secrets`) and given values out-of-band with
  `gcloud secrets versions add`. Never in `.env`, `.tfvars` committed to git, workflow files,
  or Terraform state.
- **The owner adds secret values, not you.** Writing to a secret store (and force-pushing) is
  blocked for the agent; give the owner the exact command, piping the value rather than writing
  it to disk. If a value must touch disk it goes in `.secret.local` (gitignored).
- **Public by design, not secrets:** the `NEXT_PUBLIC_*` Firebase web config and the reCAPTCHA
  site keys in `frontend/apphosting*.yaml`. Security is in the Firestore rules, App Check and
  the API's auth — not in hiding these.
- **CI authenticates keylessly** (Workload Identity Federation). Never create or commit a service
  account JSON key; `.gitignore` blocks `service-account*.json` anyway.
- **Clients never write Firestore, and the Admin SDK is server-only** — see CLAUDE.md rules 3–4.
- **GitHub secrets** hold only `TF_VAR_BILLING_ACCOUNT` and `TF_VAR_ALERT_EMAIL`; everything else CI
  needs is a non-secret repository or environment variable.
