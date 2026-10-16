---
paths:
  - ".docs/**"
  - "**/*.md"
---

# Documentation rules

`.docs/README.md` is the map. What goes where:

| Kind | Where | Mutable? |
|---|---|---|
| Architecture decision | `.docs/adr/NNNN-*.md` (`write-adr` skill) | **No** — supersede with a new ADR |
| Code-level decision ("why is this written this way") | `.docs/decisions/<area>.md` (`record-decision` skill) | Append; supersede an entry by adding a new one that links back |
| How code flows end to end | `.docs/CODE_FLOW.md` | Yes — keep it true |
| How to operate (deploy, rollback, secrets) | `.docs/RUNBOOK.md` | Yes |
| The build plan and phase checklists | `.docs/plan/` | Tick boxes; fix wrong steps in the same PR |
| Rules for Claude | `.claude/rules/`, `.claude/skills/`, `CLAUDE.md` | Yes |

- **ADRs are immutable.** Changing one means a new ADR and a 🔄 Superseded status line on the old one
  (that status line is the only edit allowed). Update both index rows in `.docs/adr/README.md`.
- **Link code with relative paths** from the doc's location. From `.docs/x.md` the repo root is
  `../`; from `.docs/plan/phases/` it's `../../../`.
- **Docs describe what is, not what was planned** — when code and a doc disagree, read the code and
  fix the doc.
- **Write for a stranger**: name the real constraint, the real cost, the file it lives in.
- **Markdown never triggers CI** (path filters exclude `**/*.md`), so a docs-only PR is cheap —
  keep it docs-only.
- The repository is public: no secrets, personal contact details, employer or client names.
