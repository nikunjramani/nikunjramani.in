---
name: pull-request
description: Branch, commit, open a PR, watch CI to green (fixing failures), and merge. Use whenever work is ready to go up for review or the owner asks to commit, push, open a PR, or merge — this repo has a protected main, a single required check, and an owner who expects CI to be driven to green without prompting.
---

# Pull request, CI, merge

## 1 · Before committing

- On a branch off an up-to-date `main` (`git checkout main && git pull && git checkout -b <type>/<topic>`).
- Docs updated in the same change (`.claude/rules/workflow.md` → "Keep the docs true").
- Local checks for what you touched: `make lint` pieces that run here; `actionlint` for workflows;
  `terraform fmt -check -recursive infra/terraform`; `make gen && git diff --exit-code` after a
  schema change. Backend tests don't run on this Windows box — CI runs them.
- `git status` — nothing unintended staged (no `.tfplan`, `.tfvars`, `.secret.local`, editor files).

## 2 · Commit and open the PR

Write the message and body to files in the scratchpad (PowerShell 5.1 mangles quoted multi-line
arguments), then:

```bash
git commit -F "$SCRATCH/commit.txt"
git push -u origin <branch>
gh pr create --title "<conventional title>" --body-file "$SCRATCH/pr.md"
```

- Title: conventional prefix (`feat:`, `fix:`, `docs:`, `ci:`, `refactor:`).
- Body: what changed and **why**, in a few lines; what the owner must do, if anything.
- End the commit and PR with the attribution lines the session asks for.

## 3 · Watch CI to the end

```bash
gh pr checks <n> --watch --fail-fast
```

Run it in the background and keep working; when it finishes, read the result. On failure:
`gh run view <run-id> --log-failed`, fix, commit, push, watch again. **Don't stop until green** —
"I pushed a fix" is not done. A `skipped` job is fine (path filters); `checks` must be green.

For an in-progress job's log: `gh api repos/<owner>/<repo>/actions/jobs/<job-id>/logs`.

## 4 · Merge

When `checks` is green and the owner hasn't said to hold:

```bash
gh pr merge <n> --squash --delete-branch
```

Then watch the `deploy` run on `main` (`gh run list --workflow deploy.yml --limit 1`) to the end
and report it. If it pauses at `production-infra`, tell the owner to approve and what the staging
apply showed.

## Don'ts

- Don't merge with red or pending required checks; don't bypass branch protection.
- Don't open one PR per dependency (`update-dependencies` skill).
- Don't add `[skip ci]`; path filters already skip what a change doesn't touch.
