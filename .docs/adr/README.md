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
| [0005](./0005-reads-bypass-python.md) | Reads bypass Python entirely | 🔄 Superseded by 0022 (caching consequence by 0014) | 2026-09-06 |
| [0006](./0006-json-schema-source-of-truth.md) | JSON Schema as the single source of truth | ✅ Accepted | 2026-09-06 |
| [0007](./0007-deny-all-client-writes.md) | All client writes denied, including admin | ✅ Accepted | 2026-09-06 |
| [0008](./0008-projects-drop-start-end-dates.md) | Projects drop start/end dates | ✅ Accepted | 2026-09-06 |
| [0009](./0009-admin-panel-is-launch-scope.md) | Admin panel is launch scope | ✅ Accepted | 2026-09-06 |
| [0010](./0010-no-monorepo-tooling.md) | No monorepo tooling | ✅ Accepted | 2026-09-06 |
| [0011](./0011-domain-wise-separate-functions.md) | Domain-wise separate Firebase Functions | ✅ Accepted | 2026-09-06 |
| [0012](./0012-generic-content-crud-in-shared.md) | Generic content CRUD lives in shared/, not per domain | ✅ Accepted | 2026-09-22 |
| [0013](./0013-local-source-app-hosting.md) | Deploy App Hosting from local source | ✅ Accepted | 2026-10-10 |
| [0014](./0014-request-scoped-content-cache.md) | Render mutable content per request | ✅ Accepted — webhook clause superseded by 0015 | 2026-10-10 |
| [0015](./0015-remove-revalidation-webhook.md) | Remove the cache-revalidation webhook | ✅ Accepted | 2026-10-13 |
| [0016](./0016-content-domains-from-a-factory.md) | Build standard content domains from their model; keep Firestore in repositories | 🔄 Structure superseded by 0017 | 2026-10-13 |
| [0017](./0017-bounded-context-domains.md) | Organise the backend as isolated domains of self-contained subdomains | ✅ Accepted | 2026-10-13 |
| [0018](./0018-staging-project-for-pr-previews.md) | A separate Firebase project for PR preview deploys | ✅ Accepted | 2026-10-13 |
| [0019](./0019-ci-identities-gated-by-github-environment.md) | CI identities are gated by GitHub environment, and CI applies Terraform | ✅ Accepted | 2026-10-15 |
| [0020](./0020-app-check-replaces-turnstile.md) | Firebase App Check replaces Cloudflare Turnstile on the contact form | ✅ Accepted | 2026-10-16 |
| [0021](./0021-site-and-admin-are-separate-surfaces.md) | The public site and the admin are separate surfaces with their own root layouts | ✅ Accepted | 2026-10-16 |
| [0022](./0022-backend-owns-all-data-access.md) | The Python API owns every read and write; the frontend never touches Firestore | ✅ Accepted | 2026-10-20 |
| [0023](./0023-backend-as-one-cloud-run-service.md) | Run the backend as one FastAPI service on Cloud Run, keeping its domains and subdomains | 🟡 Proposed | 2026-10-21 |

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

Not every project decision needs one. Plain configuration or scope calls (a project id,
which inbox gets contact-form mail, whether the repo is public) aren't architectural —
only decisions a stranger would reasonably ask *"why is it like this?"* about belong here.
