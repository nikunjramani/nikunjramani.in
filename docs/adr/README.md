# Architecture Decision Records

Every architectural decision on this project lives here — one file each, numbered and immutable.

**When something architectural changes, an ADR gets written.** Not a comment, not a commit
message, not a Slack thread. Anything that took more than ten minutes of thinking, or that a future
reader would reasonably ask "why on earth is it like this?", belongs here.

---

## Index

| # | Decision | Status | Date |
|---|---|---|---|
| [0001](./0001-nextjs-instead-of-flutter-web.md) | Next.js instead of Flutter Web | ✅ Accepted | 2026-09-06 |
| [0002](./0002-firebase-functions-instead-of-cloud-run.md) | Firebase Functions instead of standalone Cloud Run | ✅ Accepted | 2026-09-06 |
| [0003](./0003-fastapi-in-a-single-function.md) | FastAPI inside a single HTTP function | 🔄 Superseded by 0011 | 2026-09-06 |
| [0004](./0004-python-313.md) | Python 3.13 as the runtime | ✅ Accepted | 2026-09-06 |
| [0005](./0005-reads-bypass-python.md) | Reads bypass Python entirely | ✅ Accepted | 2026-09-06 |
| [0006](./0006-json-schema-source-of-truth.md) | JSON Schema as the single source of truth | ✅ Accepted | 2026-09-06 |
| [0007](./0007-deny-all-client-writes.md) | All client writes denied, including admin | ✅ Accepted | 2026-09-06 |
| [0008](./0008-projects-drop-start-end-dates.md) | Projects drop start/end dates | ✅ Accepted | 2026-09-06 |
| [0009](./0009-admin-panel-is-launch-scope.md) | Admin panel is launch scope | ✅ Accepted | 2026-09-06 |
| [0010](./0010-no-monorepo-tooling.md) | No monorepo tooling | ✅ Accepted | 2026-09-06 |
| [0011](./0011-domain-wise-separate-functions.md) | Domain-wise separate Firebase Functions | ✅ Accepted | 2026-09-06 |

**Status:** 🟡 Proposed · ✅ Accepted · ⛔ Rejected · 🔄 Superseded · ⚠️ Deprecated

---

## Writing a new one

1. Copy [`TEMPLATE.md`](./TEMPLATE.md) to `NNNN-short-kebab-title.md`, next number in sequence
2. Fill it in — **Context** and **Consequences** matter more than **Decision**
3. Add a row to the index above
4. Commit it in the same PR as the change it describes

### Rules

- **ADRs are immutable.** Never edit an accepted one to reflect a change of mind. Write a new ADR
  and mark the old one 🔄 Superseded with a link. The record of what you believed at the time *is*
  the value.
- **Record the alternatives you rejected**, and why. Six months from now, "why not X?" is the
  question you'll actually be asking.
- **Record the cost you accepted.** Every real decision has one. An ADR with no downside listed is
  an ADR that hasn't been thought through.
- One decision per file.
- Write for a stranger — which includes you, next year.

### What deserves an ADR

✅ Framework, language or datastore choices · data model shape · security posture ·
auth model · deployment topology · anything you'd have to justify in a code review

❌ Naming a variable · picking a colour · adding a dependency that does an obvious job ·
anything trivially reversible

---

Open questions not yet decided live in
[`docs/plan/decisions.md`](../plan/decisions.md). Once answered, the ones that are
architectural become ADRs here.
