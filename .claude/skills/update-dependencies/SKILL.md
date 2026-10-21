---
name: update-dependencies
description: Update npm, Python, GitHub Action, firebase-tools or Terraform provider versions. Use whenever any version is added, bumped or pinned — every version must be looked up live, and all updates go in one PR.
---

# Updating dependencies

## Rules

- **Every version is looked up live**, at the moment you write it. Memory is not a source — this
  is the project's most repeated mistake.
- **One PR for everything** being updated. No Dependabot, no per-package PRs.
- Majors that need code changes are their own migration PR, named as such.

## Where versions live, and how to look them up

| What | Where | Look up |
|---|---|---|
| Frontend npm | `frontend/package.json` | `npm view <pkg> version` / `npm outdated` in `frontend/` |
| Codegen npm | `architecture/codegen/package.json` | same, in that folder |
| Rules tests npm | `infra/rules/tests/package.json` | same |
| Python | `backend/pyproject.toml` + `uv.lock` | `uv lock --upgrade`, then read the lock diff |
| GitHub Actions | `.github/workflows/*.yml`, `.github/actions/*/action.yml` | `gh api repos/<owner>/<repo>/releases/latest --jq .tag_name` |
| firebase-tools | `.github/actions/*/action.yml` (`npm install -g firebase-tools@x`) | `npm view firebase-tools version` |
| Terraform providers | `infra/terraform/envs/*/backend.tf` | registry.terraform.io (hashicorp/google, google-beta) |
| Node | `.nvmrc`, `frontend/package.json` `engines` | the App Hosting docs' supported Node versions, then nodejs.org |
| Python | `.python-version`, `backend/Dockerfile` (`python:` image, `uv` image) | python.org + Docker Hub `library/python` tags; `gh api repos/astral-sh/uv/releases/latest` |

## Steps

1. Branch `chore/update-dependencies`.
2. Look up and update every ecosystem above; regenerate lockfiles.
3. Read the changelogs of anything that moved a major or minor; note breaking changes.
4. `make gen` (codegen tool versions can change output) and commit the result.
5. One PR (`pull-request` skill). Its single run — all checks, both plans, a staging preview —
   is the proof. Fix until green.
