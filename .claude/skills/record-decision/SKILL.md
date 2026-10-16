---
name: record-decision
description: Record a code-level decision in .docs/decisions/ and keep .docs/CODE_FLOW.md true. Use after writing or changing code whose shape a reader would question ("why is it written like this?"), after fixing a non-obvious bug, or whenever a request path, deploy path or file location changes. For architecture-level choices use write-adr instead (or as well).
---

# Recording a code decision

ADRs (`.docs/adr/`) hold architecture. **`.docs/decisions/`** holds the smaller "why is the code
written this way" choices — the ones that otherwise live only in a commit message or a code
comment. `.docs/CODE_FLOW.md` holds how requests and deploys move through the code.

## Which file

| Area | File | Prefix |
|---|---|---|
| Python functions, kernel, domains | `.docs/decisions/backend.md` | `BE-` |
| Next.js site and admin | `.docs/decisions/frontend.md` | `FE-` |
| Terraform, Firestore rules, GCP | `.docs/decisions/infra.md` | `IN-` |
| Workflows, actions, deploys | `.docs/decisions/ci-cd.md` | `CI-` |
| Schemas, codegen | `.docs/decisions/schemas-codegen.md` | `SC-` |

## Entry format

Append at the end of the right section; numbers are never reused.

```markdown
### BE-39 · <the decision, stated as what the code does>

- **Where:** [path/to/file.py](../../backend/functions/path/to/file.py) — the symbol
- **Decision:** what the code does, in one or two sentences.
- **Why:** the constraint or failure that forced it — the real one, specifically.
- **Outcome:** what it buys, and what it costs.
- **Related:** ADR NNNN · BE-12 · lessons-learned (if a mistake prompted it)
- **Since:** YYYY-MM-DD
```

## Changing your mind

Don't rewrite an entry's reasoning. Add a new entry, and mark the old one's heading
`~~BE-07~~ Superseded by BE-40` with a link. Typos and moved file paths may be fixed in place.

## CODE_FLOW.md

If the change alters a request path, trigger, deploy step, or where something lives, edit the
matching section of `.docs/CODE_FLOW.md` in the same PR. Its diagrams are text — keep them
accurate rather than complete.

## Test

Would a stranger reading the code ask "why on earth is it like this?" If yes, it gets an entry.
A variable name, an obvious library call or a trivially reversible choice doesn't.
