# CI/CD decisions

GitHub Actions. Root: [.github/](../../.github/). Flow: [CODE_FLOW §12](../CODE_FLOW.md#12--cicd);
operations: [RUNBOOK](../RUNBOOK.md#cicd-and-staging). Entries CI-01…CI-15 were backfilled on
2026-10-16 from the workflows and their history.

### CI-01 · Thin workflows; steps in composite actions

- **Where:** [.github/workflows/](../../.github/workflows/) (`pr.yml`, `deploy.yml`), [.github/actions/](../../.github/actions/)
- **Decision:** six composite actions (`schema-check`, `backend-checks`, `frontend-checks`,
  `terraform-plan`, `terraform-apply`, `firebase-deploy`) called from two workflows.
- **Why:** the owner rejected both a single monolithic workflow and `_`-prefixed reusable workflows;
  composite actions are reusable steps with their own folder and inputs.
- **Since:** 2026-10-15 · **Related:** lessons-learned

### CI-02 · Configuration is read from where it already lives

- **Where:** `firebase-deploy` (`--project <alias>` from `.firebaserc`), `frontend-checks`
  (`yq` over `frontend/apphosting.yaml`), GitHub environment variables (`SITE_URL`, `WIF_PROVIDER`,
  `DEPLOY_SA`, `TERRAFORM_SA`)
- **Why:** a project id or URL copied into a workflow drifts from the real one.

### ~~CI-03~~ Superseded by [CI-16](#ci-16--the-api-deploys-as-an-image-first-and-rolls-back-by-revision) · Path filters decide what runs and what deploys — and markdown never does

- **Where:** the `changes` job in both workflows (`dorny/paths-filter@v4`)
- **Decision:** check filters (`schemas`, `backend`, `frontend`, `infra`) and deploy-target filters
  (`rules`, `functions`, `apphosting`), identical across `pr.yml` and `deploy.yml`. A `.github/**`
  change matches everything. Code filters end with `'!**/*.md'` under
  `predicate-quantifier: some-with-excludes`.
- **Why:** a design change shouldn't run backend tests or redeploy functions; a docs change
  shouldn't run anything. Before the exclusion, a README under `backend/` ran backend CI and
  redeployed every function.
- **Since:** 2026-10-16 (markdown exclusion: this entry's PR) · **Related:** RUNBOOK "What runs for what"

### CI-04 · One required status check: `checks`

- **Where:** `checks` job in pr.yml
- **Decision:** `needs` every check job, `if: always()`, passes when each result is `success` or `skipped`.
- **Why:** branch protection then names one stable check while jobs are added, renamed or matrixed
  (`infra-plan (prod)`), and a job that failed — or was cancelled — anywhere in the graph fails it.
  Docs-only PRs still get a `checks` result, which a path-filtered *workflow* would never report.

### CI-05 · Previews deploy to one shared staging slot; fork PRs never reach it

- **Where:** `preview` job (`concurrency: staging`, `cancel-in-progress: true`, same-repo condition)
- **Why:** one staging project is enough for a single maintainer; forks get no OIDC token, so they
  couldn't authenticate anyway — the condition makes that explicit.
- **Related:** ADR 0018

### CI-06 · The PR comment comes from an action, not a script

- **Where:** `marocchino/sticky-pull-request-comment` in pr.yml and `terraform-plan`
- **Why:** the owner's rule — no scripts where an action exists. Sticky means one comment updated in place.
- **Since:** 2026-10-15

### CI-07 · Lighthouse is report-only on staging

- **Where:** `treosh/lighthouse-ci-action` in the preview job
- **Why:** staging is `noindex` and scales to zero, so its scores aren't prod's; failing PRs on them
  would be noise. Reports land as run artifacts — never committed.

### CI-08 · Deploys retry three times, 90 s apart

- **Where:** "Deploy" step in [actions/firebase-deploy](../../.github/actions/firebase-deploy/action.yml)
- **Why:** a fresh project's first deploys hit documented propagation races (Eventarc service agent,
  `gcf-artifacts`, the source bucket) whose remedy is "retry in a few minutes".

### CI-09 · Every deploy ends in a smoke test of `/` and the health endpoint

- **Where:** "Smoke test" step (curl with retries)
- **Why:** proves both App Hosting and the function path through the rewrite answer; its failure
  triggers the rollback (CI-10).

### CI-10 · Rollback redeploys the previous commit with the *current* deploy action

- **Where:** `rollback` job in deploy.yml (two checkouts: previous code, current `.github/actions` sparse)
- **Why:** the previous commit's own action might be the broken part; the current one is known to
  run. Terraform is not rolled back — infra changes are reviewed at the approval step.

### ~~CI-11~~ Superseded by [CI-16](#ci-16--the-api-deploys-as-an-image-first-and-rolls-back-by-revision) · Terraform applies after the code deploy, staging first, prod behind approval

- **Where:** `terraform` job in deploy.yml (`max-parallel: 1`, `production-infra` environment)
- **Decision:** runs when `infra/terraform/**` changed (or manual `infra_only`), accepting a
  `skipped` deploy; staging's apply is the rehearsal for prod's.
- **Why:** invoker bindings need deployed functions (IN-05). The exception — a new secret a function
  binds — is handled by running `infra_only` first.
- **Related:** ADR 0019

### CI-12 · Production deploys have an off switch

- **Where:** `vars.PROD_DEPLOY_ENABLED` on the `changes` job of deploy.yml
- **Why:** prod had un-deployed changes when CI was built; deploys stayed off until it caught up.
  On since 2026-10-16. Deleting the variable pauses prod deploys without editing workflows.

### CI-13 · Versions are looked up live and pinned; updates go in one PR

- **Where:** every `uses:`; `firebase-tools@<exact>` in the actions
- **Decision:** actions on verified current major tags; `firebase-tools` pinned exactly; no Dependabot.
- **Why:** versions recalled from memory were already stale when pinned; Dependabot's per-package
  PRs burned CI. → `update-dependencies` skill.
- **Since:** 2026-10-15 · **Related:** lessons-learned

### CI-14 · A production deploy is never cancelled mid-flight

- **Where:** `concurrency: production`, `cancel-in-progress: false` in deploy.yml (PRs cancel stale runs instead)
- **Why:** a half-finished deploy (rules done, functions half-rolled) is worse than a queued one.

### CI-15 · Backend tests run under the Firestore emulator in CI

- **Where:** [actions/backend-checks](../../.github/actions/backend-checks/action.yml) — `firebase emulators:exec --only firestore`
- **Why:** the repository and integration tests need a real Firestore; they skip without the
  emulator, so CI is where they always run (they can't run on the owner's Windows machine).

### CI-16 · The API deploys as an image, first, and rolls back by revision

- **Where:** [actions/cloud-run-deploy](../../.github/actions/cloud-run-deploy/action.yml); the `api` filter and job order in `pr.yml` and `deploy.yml`
- **Decision:** the deploy targets are `rules`, `api` (was `functions`) and `apphosting`, still
  identical across both workflows, markdown still excluded (as CI-03). `api` matches
  `backend/**`, `architecture/**`, the Makefile and `.firebaserc`. It deploys first: build
  `backend/Dockerfile` with buildx (GitHub Actions cache), push
  `<region>-docker.pkg.dev/<project>/backend/api:<sha>`, `make deploy-api`, smoke-test
  `/api/v1/ops/health` on the service URL; on failure, traffic goes back to the revision that
  was serving before. `firebase-deploy` then does rules and App Hosting only. Terraform still
  applies after the code deploy, staging first, prod behind approval (as CI-11), because it
  creates the Eventarc triggers and scheduler job that point at the CI-created service.
- **Why:** the site deployed next calls the API, so the API must be live first; rolling back a
  revision is seconds and needs no rebuild, where re-running `firebase deploy` from an old
  commit rebuilt functions. The project comes from `.firebaserc` and the region from the
  Makefile, so the action holds no environment value (CI-02).
- **Outcome:** an API-only change no longer runs the Firebase CLI. Cost: the service exists only
  after its first deploy — in a fresh project the API must deploy before the first full apply.
- **Related:** ADR 0023 · BE-45 · IN-16 · supersedes CI-03 (target names) and CI-11 (reason)
- **Since:** 2026-10-21
