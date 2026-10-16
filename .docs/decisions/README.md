# Code decisions

Why the code is written the way it is — one entry per non-obvious choice, with the reason and
what it cost. [ADRs](../adr/README.md) hold the architectural decisions (framework, topology,
security posture); this log holds everything below that line that a reader would still ask
"why is it like this?" about. How the pieces connect: [CODE_FLOW.md](../CODE_FLOW.md).

| Area | File | Entries |
|---|---|---|
| Backend — Python functions, kernel, domains | [backend.md](./backend.md) | `BE-` |
| Frontend — Next.js site and admin | [frontend.md](./frontend.md) | `FE-` |
| Infrastructure — Terraform, rules, GCP | [infra.md](./infra.md) | `IN-` |
| CI/CD — workflows, actions, deploys | [ci-cd.md](./ci-cd.md) | `CI-` |
| Schemas and codegen | [schemas-codegen.md](./schemas-codegen.md) | `SC-` |

## Entry format

```markdown
### BE-12 · What the code does, stated as the decision

- **Where:** link to the file (and symbol)
- **Decision:** what, in a sentence or two
- **Why:** the real constraint or failure that forced it
- **Outcome:** what it buys — and what it costs
- **Related:** ADRs, other entries, lessons-learned
- **Since:** date (entries recorded on 2026-10-16 were backfilled from the code and git history)
```

## Keeping it true

- Every PR that makes a choice like these adds an entry (`record-decision` skill).
- Numbers are never reused. To change a decision, add a new entry and mark the old heading
  `~~BE-07~~ Superseded by BE-40` — the reasoning that was believed at the time stays readable.
- Moved file paths and typos may be fixed in place.
