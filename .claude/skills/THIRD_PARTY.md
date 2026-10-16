# Third-party skills

Vendored copies, read in full before committing (2026-10-16). Each is pinned to the commit it was
copied from — to update one, fetch that file at a newer commit, read the whole diff, and change
the SHA here. Never point a skill at a live URL: an instruction that can change without a commit
is an instruction nobody reviewed.

| Skill | Source | Commit | Licence | Changes here |
|---|---|---|---|---|
| `frontend-design` | [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | `dbd4588f9e1033efb41dad4bef2f7947c8993d44` | Apache-2.0 (`frontend-design/LICENSE.txt`) | none |
| `react-best-practices` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices) | `063bee94c3f4df8453406c830b0a7df0f2860278` | MIT (declared in the skill's frontmatter and the repository README) | compiled `AGENTS.md` and `rules/_template.md` left out; a "In this project" section added to `SKILL.md` |
| `web-design-guidelines` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) + [vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines) `command.md` | `063bee94…` / `434b7f91364665f2f733b310ec54809bf8f37937` | MIT (`web-design-guidelines/LICENSE`, © 2025 Vercel Labs) | `SKILL.md` rewritten to read a local snapshot (`guidelines.md`) instead of fetching at run time; project overrides added |
| `firebase-security-rules-auditor` | [firebase/agent-skills](https://github.com/firebase/agent-skills/tree/main/skills/firebase-security-rules-auditor) | `306cc1844c47839bd4f2c7dba7cc3c394e4f3e0b` | Apache-2.0 (`firebase-security-rules-auditor/LICENSE`) | none |

Considered and left out: HashiCorp's `terraform-style-guide` (AWS-centric; `.claude/rules/infra.md`
covers this repo's conventions) and Firebase's `firebase-app-hosting-basics` (describes a
git-push setup this project replaced with CI deploys, ADR 0013/0018).

Everything else under `.claude/skills/` is this project's own.
