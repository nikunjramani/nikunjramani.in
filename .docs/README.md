# Documentation

Everything about how nikunjramani.in is built, why, and how to run it. Start with
**[CODE_FLOW.md](./CODE_FLOW.md)** to understand the code; reach for the rest when you need it.

| Doc | Read it to… |
|---|---|
| [CODE_FLOW.md](./CODE_FLOW.md) | follow any request, edit, upload, schema change or deploy through the code, file by file |
| [decisions/](./decisions/README.md) | find out **why** a piece of code is written the way it is — per area, with what it cost |
| [adr/](./adr/README.md) | read the architectural decisions (framework, topology, security posture) and what they superseded |
| [RUNBOOK.md](./RUNBOOK.md) | operate it: local dev, CI/CD and staging, deploy, rollback, secrets, admin access, backups |
| [plan/](./plan/README.md) | see the original build plan, the phase checklists and their status |

## Keeping these true

Docs change in the **same PR** as the code they describe — a flow change updates
`CODE_FLOW.md`, a non-obvious choice adds a `decisions/` entry, an architectural one adds an ADR
(`.claude/rules/workflow.md`). Markdown never triggers CI, so a docs-only PR costs nothing to run.

## For Claude

[`CLAUDE.md`](../CLAUDE.md) is the entry point. Rules load from [`.claude/rules/`](../.claude/rules/)
(always, or by the files being touched); task playbooks are skills in
[`.claude/skills/`](../.claude/skills/). Mistakes that must not recur are in
[`.claude/rules/lessons-learned.md`](../.claude/rules/lessons-learned.md).
