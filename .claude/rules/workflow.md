# How work gets done here

Loaded every session. These come from the owner's corrections — each one was a real mistake
first (see `lessons-learned.md`).

## Verify, never assume

- **Look things up live; memory is not a source.** Package, action, tool and provider versions
  come from the registry or the upstream release page *at the moment you pin them* — npm, PyPI,
  `gh api repos/<o>/<r>/releases`, the Terraform registry. Never pin a version from memory, not
  even one "you just used". Same for API behaviour, CLI flags and IAM role contents: read the
  docs or run the command (`gcloud iam roles describe …`) before relying on it.
- **Read the code before describing it.** A plan, ADR or doc can be stale; the code is the truth.
  When a doc turns out wrong, fix it in the same PR.
- **Next.js 16 is not the Next.js in your training data.** Read
  `frontend/node_modules/next/dist/docs/` before writing Next code (`frontend/AGENTS.md`).

## Pull requests

- **Branch from an up-to-date `main`**; `main` is protected — squash merges only, required check
  `checks`.
- **One PR per coherent change.** Dependency updates go in **one** PR together, never one PR per
  package. No Dependabot, no Renovate.
- **Commit and PR text from files** on Windows (`git commit -F <file>`,
  `gh pr create --body-file <file>`); PowerShell 5.1 mangles quoted multi-line arguments.
- **After pushing, watch CI to completion.** If it fails, read the log, fix, push, and watch again
  — don't stop at "it failed" or at "I pushed a fix". Done means green.
- **Merge once CI is green** (`gh pr merge <n> --squash --delete-branch`) unless the owner said to
  hold it; then confirm the `deploy` run on `main` succeeds too.
- **Don't spend CI on nothing.** Docs and `.claude/` changes run only the required `checks` job;
  keep docs-only PRs docs-only so they stay that way.

## CI and automation

- **No scripts.** Not in the repo, not as long inline `run:` blocks in workflows. If GitHub Actions
  has an action for it (PR comments, path filtering), use the action. Shell in a workflow is a
  few lines of glue at most.
- **Composite actions under `.github/actions/<name>/`**, called from thin workflows. Never
  `_`-prefixed reusable workflows, never one giant workflow file.
- **Environment config is read from its source** (`.firebaserc` aliases, `frontend/apphosting*.yaml`,
  GitHub environment variables) — never hard-coded into CI files.
- See `.claude/rules/ci.md` (loads when you touch `.github/`).

## Keep the docs true — in the same PR

Every change that alters behaviour or structure updates, in the same PR:

1. **`.docs/CODE_FLOW.md`** — if a request path, deploy path, or the place something lives changed.
2. **`.docs/decisions/<area>.md`** — a new entry (or a superseding one) for any code-level choice a
   reader would ask "why is it like this?" about. Use the `record-decision` skill.
3. **An ADR** in `.docs/adr/` if the choice is architectural (`write-adr` skill).
4. **The scoped rule or skill** in `.claude/` if the change alters how future work must be done.
5. **`lessons-learned.md`** if the change fixes a mistake that could recur.

A PR that changes code but leaves these stale is not finished.

## Talking to the owner

- Recommend; don't survey. Give the reason in a sentence.
- When something is blocked on the owner (a sign-in, a secret value, an approval), say exactly
  what to run or click, then continue with everything that isn't blocked.
- Report outcomes as they are — failed is failed, skipped is skipped.
