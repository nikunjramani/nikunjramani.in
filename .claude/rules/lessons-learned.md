# Lessons learned — mistakes not to repeat

Loaded every session. Each entry is something that actually went wrong on this project, and the
rule that prevents it. Add an entry whenever a fix lands for a mistake that could recur — newest
first within each section, with the date.

## Process

- **2026-10-20 · A data rule enforced only in the UI.** "Don't delete an image a page still uses"
  lived in a Next.js route the admin UI called first; the API's delete never checked it. →
  Rules that protect data are enforced in the API service, for every caller; the UI only
  explains them (ADR 0022).
- **2026-10-15 · Versions pinned from memory.** CI was written with action and package versions
  recalled rather than looked up; a day later "updates" were needed for versions that were already
  old when pinned. → Look up every version live at the moment of pinning (`workflow.md`). This
  is the most repeated mistake on the project.
- **2026-10-15 · One PR per dependency.** Dependabot opened a PR per package and burned CI on each.
  → Dependabot removed. All dependency updates go in one PR.
- **2026-10-15 · Stopped watching CI after pushing.** Several rounds of "still failing" from the
  owner. → Watch every run to the end; fix and re-push until green, then merge.
- **2026-10-15 · Inline scripts and a committed Lighthouse JSON in CI.** → No scripts; use
  actions (`marocchino/sticky-pull-request-comment` for PR comments). Don't commit generated reports.
- **2026-10-15 · Everything in one workflow file, then `_`-prefixed reusable workflows.** →
  Composite actions in `.github/actions/<name>/`, thin workflows.
- **2026-10-15 · Hard-coded env values in CI files.** → Read config from its source (`.firebaserc`,
  `apphosting*.yaml`, GitHub environment variables).
- **2026-10-15 · Over-built abstractions** (a `deployable` flag nobody needed). → Question every new
  flag or layer; if the owner asks "do we need this?", the answer usually was no.
- **2026-10-15 · Secrets reached git history.** History was rewritten. → `security.md`.

## Backend structure (ADR 0017)

- **2026-10-13 · Tests placed inside `src/` subdomains.** → Tests live only in
  `backend/tests/`, mirroring the source tree.
- **2026-10-13 · A `common/` folder per domain that did every job.** → No `common/` anywhere; each
  subdomain owns its slice, even if that means two small files that look alike.
- **2026-10-13 · `__init__.py` everywhere; a separate `domains/` folder instead of `src/`.** → Implicit
  namespace packages under `src/<domain>/<subdomain>/`; `__init__.py` only in `shared/generated`.
- **2026-10-13 · Models duplicated per domain.** → Models are generated once into
  `shared/generated` and imported from there.

## Infrastructure and deploys

- **2026-10-21 · Asked the owner for grants Terraform would have made itself.** Phase 9's
  prerequisites had the owner grant the apply identity roles for resource types that didn't
  exist yet; Terraform grants those in the same apply (the module depends on `module.iam`). Only
  the deploy identity's Artifact Registry role truly needed a hand: the PR preview runs before
  any apply. → Ask for a manual grant only for a refresh of an existing resource (below) or a
  role a preview needs before merge (`infra.md`).
- **2026-10-16 · Terraform can't grant itself a role it needs to *read* a resource.** The apply
  account lacked `roles/recaptchaenterprise.admin`; refresh 403'd before apply could grant it.
  PR plans passed only because the plan account has `roles/viewer`. → When a module adds a new
  resource type, check the *apply* identity's roles (`terraform_roles` in `modules/iam`), not just
  the plan's — and grant it by hand once in existing projects *if Terraform already manages a
  resource of that type* (a refresh comes before any grant).
- **2026-10-16 · `firebase deploy --only storage` on a project without Firebase Storage.** The media
  bucket is plain GCS behind IAM. → Storage rules are emulator-only; never deploy them.
- **2026-10-16 · Secret Manager rejects an empty version.** → A not-yet-configured secret gets a
  single newline; the reading settings use `str_strip_whitespace=True`.
- **2026-10-16 · mypy rejected `module.httpx` (not re-exported).** → Patch the library where it's
  defined (`httpx.post`), not through another module's namespace.
- **Earlier · Admin SDK app not created before the first `verify_id_token`.** It type-checked
  and passed unit tests, and failed only against the real emulator. → Auth changes need a real
  request against the emulators (`make dev-backend`). (The same entry used to cover a2wsgi's
  thread hanging after a fork; that adapter went with the move to Cloud Run, ADR 0023.)

## Tooling on Windows

- **PowerShell 5.1 mangles quoted multi-line native arguments** → message files (`-F`,
  `--body-file`) in the scratchpad.
- **Git Bash heredocs and `\n` escapes inside them are fragile** → use the Edit/Write tools for
  file content, not `cat <<EOF`.
- **Python's stdout is cp1252** → scripts that print `→`/`✓` crash; set
  `sys.stdout.reconfigure(encoding="utf-8")` in a throwaway one-liner, or run under CI.
- **Backend tests can't run on this Windows box** (blurhash-python needs MSVC) → CI is the test
  runner; lint what you can locally.
