# 08 · Costs & Risks

---

## Cost

Everything sits inside free tiers. **Realistic monthly cost: ₹0.**

| Service | Free tier | Our expected use |
|---|---|---|
| Firestore | 50k reads · 20k writes · 1 GiB/day | A few hundred reads/day, and ISR caches most of those away |
| Firebase Storage | 5 GB stored · 1 GB/day download | Under 500 MB of images |
| Firebase Auth | Unlimited for our use | Exactly one user — you |
| Cloud Functions | 2M invocations · 400k GB-s/mo | A few hundred invocations/month |
| App Hosting | Cloud Run free tier | Low traffic, SSR cached at the CDN |
| Resend | 3,000 emails/mo | Maybe 10 |
| Domain | — | Already bought |

### The Blaze caveat

Storage, Cloud Functions and App Hosting all **require the Blaze (pay-as-you-go) plan** — a card on
file, even though you stay inside the free allowances. This is unavoidable, not a choice in the plan.

So Phase 0 sets up:

- A **₹500 budget alert** notifying at 50%, 90% and 100%
- Function `max_instances = 3`
- Storage lifecycle rules capping backup growth
- Firestore TTL on `contact_messages`

With those in place, the realistic worst case from a bug or a bot is a notification email, not a
bill.

### What would actually cost money

Honestly, for this to cost anything meaningful you'd need real traffic — tens of thousands of
visitors a month. At that point the site is doing its job and a few hundred rupees is a good problem.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Content never gets written** | High | Project stalls at 90% | [Phase 2](./phases/phase-2-content-design.md) is explicitly a content phase with a checklist. Start it early, run it in parallel |
| **Next.js/React learning curve** | Medium | Slower Phase 4–5 | Phases ordered so you learn on the simpler public site before the admin panel. Generous comments, ADRs for non-obvious calls |
| **Admin panel scope creep** | Medium | Launch slips | [Phase 5](./phases/phase-5-admin-panel.md) has a fixed route list. Anything else goes to Phase 8 |
| **Schema churn early on** | Medium | Rework | Versioning from Phase 1. Churn is cheap *because* it's centralised — that's the point of the architecture folder |
| **Terraform partial coverage** | Certain | Confusion in Phase 0 | [04 · Infrastructure](./04-infrastructure.md) lists the manual steps explicitly; `bootstrap.sh` scripts what it can |
| **Function cold start (1–3s)** | Certain | Slow contact submit | Write path only. Never blocks a page load. Spinner covers it |
| **Perfectionism on design** | Medium | Launch slips | Ship at "good", iterate live. The site is editable without a deploy — that's the whole point |
| **Contact form spam** | High | Inbox noise | Five stacked defences — [03 · Security](./03-security.md) |
| **Runaway cost from a bug** | Low | Bill | max_instances, budget alerts, TTLs |
| **Losing content** | Low | Painful | Nightly Firestore export, 30-day retention, weekly verification |

---

## The two that actually matter

Most of that table is routine. Two are worth genuinely watching:

**Content.** This is the single most common reason personal sites never ship. The build will be
done and the site will sit unlaunched because the About page says "Lorem ipsum". Mitigation: start
[06 · Content Checklist](./06-content-checklist.md) *now*, in parallel with Phase 0, and write badly
first.

**Scope.** Every feature is defensible in isolation — a blog, testimonials, analytics, view counts,
i18n. Together they mean launching in six months instead of six weeks. The phase boundaries exist to
be enforced, not admired. Launch at the end of Phase 6, then add things to a live site.

---

**Back to:** [Plan index](./README.md) · **Start:** [Phase 0](./phases/phase-0-foundation.md)
