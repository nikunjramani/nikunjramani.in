# Open Decisions

Questions still blocking [Phase 0](./phases/phase-0-foundation.md).

> **Settled decisions live in [`docs/adr/`](../adr/README.md)**, one file each, with the
> alternatives rejected and the cost accepted. Ten are recorded so far.

---

## ⏳ Needed before Phase 0

| # | Question | Recommendation | Answer |
|---|---|---|---|
| 1 | Next.js 16 + TypeScript as the frontend? | **Yes** — solves SEO, most transferable skill · [ADR 0001](../adr/0001-nextjs-instead-of-flutter-web.md) | |
| 2 | FastAPI in one Function, or many small plain Functions? | **FastAPI in one** · [ADR 0003](../adr/0003-fastapi-in-a-single-function.md) | |
| 3 | Firebase project id | `nikunjramani-in` | |
| 4 | Staging environment, or prod only? | **Prod only** — modules make staging a 1-day add later | |
| 5 | Enable Blaze + ₹500 budget alert? | **Yes** — required for Storage/Functions/App Hosting; real cost ₹0 | |
| 6 | Admin panel at launch? | **Yes** · [ADR 0009](../adr/0009-admin-panel-is-launch-scope.md) | |
| 7 | Blog at launch? | **No** — [Phase 8](./phases/phase-8-post-launch.md) | |
| 8 | Contact email destination | Your existing inbox now → `hello@nikunjramani.in` later | |
| 9 | GitHub repo public or private? | **Public** — it's a portfolio piece in itself | |
| 10 | Anything from [06 · Content](./06-content-checklist.md) already written? | Send it and we skip ahead | |

Answer inline in the table, or say **"approved, defaults are fine"** to take every recommendation
as written.

---

## How a decision becomes an ADR

Not everything here needs one. The test is whether a stranger — including you next year — would ask
*"why on earth is it like this?"*

```
Open question here
        │
        ├── architectural?  ──▶  write docs/adr/NNNN-….md, remove the row
        │
        └── just a preference?  ──▶  answer it, note it in the relevant plan doc
```

Of the ten questions above, #1, #2, #6 and #7 are architectural and already have ADRs backing the
recommendation. #3, #5, #8 and #9 are configuration. #4 and #10 are scope.

See [`docs/adr/README.md`](../adr/README.md) for the rules and the template.
