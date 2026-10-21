# Build Plan — nikunjramani.in

The plan lives here, split by topic and phase. Start with the
[Overview](./00-overview.md), then work the phases in order.

---

## Reference — read once, refer back often

| # | Doc | What's in it |
|---|---|---|
| 00 | [Overview](./00-overview.md) | The decisions, the stack, the architecture diagram |
| 01 | [Repo Architecture](./01-repo-architecture.md) | Folder layout and the layering rules that keep it clean |
| 02 | [Data Model](./02-data-model.md) | Schema-first approach, every collection, the project model |
| 03 | [Security](./03-security.md) | Firestore rules, admin auth, secrets, spam defence |
| 04 | [Infrastructure](./04-infrastructure.md) | Terraform modules, what it can't cover, guardrails |
| 05 | [CI/CD](./05-cicd.md) | Workflows, Workload Identity Federation, branch protection |
| 06 | [Content Checklist](./06-content-checklist.md) | **What you actually need to write** |
| 07 | [Domain Setup](./07-domain-setup.md) | GoDaddy → Firebase DNS, step by step |
| — | [ADRs](../adr/README.md) | Architecture decision records — twenty-three and counting |
| — | [Code flow](../CODE_FLOW.md) · [Code decisions](../decisions/README.md) | How the built code flows end to end, and why it's written as it is |

## Phases — work these in order

| Phase | Doc | Hours | Status |
|---|---|---|---|
| 0 | [Foundation & Infra](./phases/phase-0-foundation.md) | ~6h | ✅ Done |
| 1 | [Schemas & Codegen](./phases/phase-1-schemas.md) | ~7h | ✅ Done |
| 2 | [Content & Design](./phases/phase-2-content-design.md) | ~5h | 🟡 Technical design built; copy live via admin; `/styleguide` open |
| 3 | [Backend](./phases/phase-3-backend.md) | ~14h | ✅ Done |
| 4 | [Public Site](./phases/phase-4-public-site.md) | ~16h | 🟡 Built & verified; blocked on Phase 2 content + Phase 6 Lighthouse |
| 5 | [Admin Panel](./phases/phase-5-admin-panel.md) | ~14h | 🟡 Built; production admin claim and signed uploads verified |
| 6 | [Deploy & DNS](./phases/phase-6-deploy.md) | ~5h | 🟡 `nikunjramani.in` live over HTTPS; a few launch checks remain |
| 7 | [CI/CD Hardening](./phases/phase-7-cicd.md) | ~5h | 🟡 PR checks, staging previews and prod deploys live (prod since 2026-10-16) |
| 8 | [Post-Launch](./phases/phase-8-post-launch.md) | ongoing | ⬜ Not started |
| 9 | [Backend on Cloud Run](./phases/phase-9-cloud-run-backend.md) | one PR | ✅ Done 2026-10-21 |

**Launch is the end of Phase 6.** Total: ~67h of build + ~5h of your writing.

Hours are focused working time, not calendar time.

---

## How the phases fit together

```
  0 ──▶ 1 ──▶ 3 ──▶ 4 ──▶ 5 ──▶ 6 ──▶ 7
       infra   API   site  admin deploy  CI
        │
        └──▶ 2 (content & design — runs in parallel, blocks Phase 4)
```

Phase 2 is mostly **your** writing time, not build time. Start it early and let it run
alongside Phases 1 and 3 — it's the thing most likely to stall the project at 90% done.

## Conventions in these docs

- **Goal** — one sentence on why the phase exists
- **Prerequisites** — what must be true before starting
- **Tasks** — checkboxes; tick them as we go
- **Definition of done** — the objective test that the phase is finished
- **Gotchas** — things that will bite, noted in advance

## Status legend

⬜ Not started · 🟡 In progress · ✅ Done · ⛔ Blocked
