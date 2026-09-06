# Decisions

All ten opening questions are answered. **Phase 0 is unblocked.**

> Settled architectural decisions live in [`docs/adr/`](../adr/README.md), one file each, with the
> alternatives rejected and the cost accepted. Eleven are recorded.

---

## ✅ Answered — 2026-09-06

| # | Question | Decision |
|---|---|---|
| 1 | Frontend | **Next.js 16 + TypeScript** · [ADR 0001](../adr/0001-nextjs-instead-of-flutter-web.md) |
| 2 | API shape | **Changed** — one function *per domain*, not one for the whole API · [ADR 0011](../adr/0011-domain-wise-separate-functions.md) |
| 3 | Firebase project id | `nikunjramani-in` |
| 4 | Environments | **Prod only.** No staging for now |
| 5 | Billing | **Deferred.** Blaze not enabled yet — see the note below. Blocks Phase 6 only |
| 6 | Admin panel at launch | **Yes** · [ADR 0009](../adr/0009-admin-panel-is-launch-scope.md) |
| 7 | Blog at launch | **No** — [Phase 8](./phases/phase-8-post-launch.md) |
| 8 | Contact email | Existing inbox for now → `hello@nikunjramani.in` later |
| 9 | GitHub repo | **Public** |
| 10 | Existing content | None yet — [Phase 2](./phases/phase-2-content-design.md) writes it |

### ⚠️ Billing is deferred — and that is fine until Phase 6

Firebase **Storage, Cloud Functions and App Hosting cannot be enabled on the Spark plan at all**.
Blaze — a card on file — is mandatory even to stay entirely within the free allowances. There is no
version of this stack without it.

**But the Firebase emulators need no billing.** Firestore, Auth, Storage and Functions all run
locally, so Phases 1–5 can be built and tested in full against emulated services:

| Phase | Needs billing? |
|---|---|
| 1 · Schemas & codegen | No — pure JSON Schema and generators |
| 2 · Content & design | No |
| 3 · Backend | No — the whole API and its tests run on the emulator |
| 4 · Public site | No — reads from the emulator |
| 5 · Admin panel | No — writes to the emulator |
| **6 · Deploy** | **Yes.** This is the wall |

So roughly 50 hours of work is available before money is involved. Enable Blaze when Phase 6 is
actually in reach, not before.

When that time comes, the expected bill is **₹0**, and these guardrails are what keep it there:

- Budget alert at ₹500, notifying at 50 / 90 / 100%
- `max_instances = 3` per function domain
- Storage lifecycle rules capping backup growth
- Firestore TTL on `contact_messages`

Full breakdown: [08 · Costs & Risks](./08-costs-and-risks.md).

---

## How a decision becomes an ADR

The test is whether a stranger — including you, next year — would ask *"why on earth is it like
this?"*

Of the ten above, #1, #2, #6 and #7 are architectural and have ADRs. #3, #5, #8 and #9 are
configuration. #4 and #10 are scope.

See [`docs/adr/README.md`](../adr/README.md) for the rules and the template.
