# Phase 6 · Deploy & DNS

**~5 hours** · Status: 🟡 In progress — 2026-10-10 · **🚀 LAUNCH**

> **Goal:** nikunjramani.in live on your domain, over HTTPS, indexed by Google,
> with link previews that look right.

⛔ **This is the phase that needs Blaze billing.** Everything before it runs on the emulators.
Blaze is enabled. See [Deploy Progress](../DEPLOY-PROGRESS.md) for current state.

---

## Prerequisites

- [ ] Phases 0–5 done
- [x] [07 · Domain Setup](../07-domain-setup.md) read
- [ ] GoDaddy DNS access to hand

---

## Tasks

### 6.1 · Infrastructure

- [x] Fill in `modules/functions` — `for_each` over the domain map, per-domain memory and
      `max_instances = 3`, secrets bound. Took two real fixes once applied against the
      actual project: the IAM binding was targeting the Cloud Run v1 API (2nd-gen
      Functions are v2) and the underscored function id (`api_system`) isn't the real
      Cloud Run service name (`api-system` — DNS-safe hyphenation).
- [ ] Fill in `modules/app-hosting` — backend, GitHub connection, env vars. Module and
      the Firebase Web App registration are done; the backend resource itself is still
      a no-op pending the console GitHub connection (Part E).
- [x] `terraform plan` reviewed
- [x] `terraform apply` — budget alert (₹100/mo), WIF pool + deploy SA, Firestore
      database, 2 storage buckets, 4 secret containers, error-rate alert, 12 public
      invoker bindings, all live on `nikunjramani-in`
- [ ] Uptime check and alerts confirmed active — error-rate alert is live and
      confirmed (log-based metric + alert policy). The uptime check itself needs the
      real public health path, which only exists once Part 6.3's rewrite is live —
      deferred to 6.6's smoke tests rather than monitoring a throwaway raw-function URL

### 6.2 · Backend deploy

- [ ] Secrets populated in Secret Manager (Resend, Turnstile) — deliberately deferred;
      `REVALIDATE_TOKEN` and `CONTACT_EMAIL_TO` are populated (no third-party account
      needed for either)
- [x] `firebase deploy --only functions` — all 12 domains + 2 triggers + the scheduled
      backup, confirmed via `firebase functions:list`, none silently skipped
- [ ] `next.config.ts` rewrites resolve for every domain — needs `FUNCTIONS_BASE_URL`
      set in `apphosting.yaml` (6.3) before this is testable for real
- [x] `/health` responds on the deployed URL — verified directly against the raw
      Cloud Function (`.../api_system/health` → `{"environment":"production"}`); via
      the rewrite specifically still needs 6.3
- [ ] A real contact submission delivers an email — blocked on the deferred Resend key
- [x] Scheduled backup manually triggered on 2026-10-10; HTTP 200 and all 11 JSON exports verified in the private backup bucket.
- [x] `/docs` confirmed **disabled** in production — a real gap, not a formality: the
      first deploy had `/docs` and `/openapi.json` publicly reachable on all 12
      domains because nothing set `ENVIRONMENT=production` at deploy time. Fixed via
      `backend/functions/.env.nikunjramani-in` and reverified — both now 404

### 6.3 · Frontend deploy

- [x] `frontend/apphosting.yaml` — framework build detection, Node 22, build/runtime env, scale to zero, max 3 instances
- [ ] Optional: connect GitHub for automatic rollouts. Manual deployment uses local source (ADR 0013).
- [ ] First build succeeds
- [ ] Site reachable on the default App Hosting URL
- [ ] Server-side env vars confirmed **not** in the client bundle

### 6.4 · DNS

Follow [07 · Domain Setup](../07-domain-setup.md).

- [ ] Custom domain added in Firebase for apex and `www`
- [ ] TXT verification record added at GoDaddy
- [ ] Both A records added
- [ ] `CNAME www → nikunjramani.in`
- [ ] **GoDaddy parking records and forwarding deleted** ⚠️
- [ ] Verification passed
- [ ] SSL provisioned
- [ ] `www` → apex redirect confirmed
- [ ] Optional: `api.nikunjramani.in` CNAME

### 6.5 · SEO go-live

- [ ] Google Search Console — property verified
- [ ] `sitemap.xml` submitted
- [ ] `robots.txt` correct and reachable
- [ ] Rich Results Test passes on the JSON-LD
- [ ] LinkedIn Post Inspector shows the right preview
- [ ] WhatsApp / iMessage previews checked on a phone
- [ ] Canonical URLs consistent across every page

### 6.6 · Smoke tests

- [ ] Every public route loads over HTTPS
- [ ] A project detail page renders fully
- [ ] Contact form → email received
- [ ] Résumé download works
- [ ] `/admin` login works on the live domain
- [ ] An edit in `/admin` appears on the public site within seconds
- [ ] Lighthouse run against **production**, not localhost
- [ ] 404 page works
- [ ] Mobile check on a real device

### 6.7 · Runbook

- [ ] `docs/RUNBOOK.md` — deploy, rollback, rotate secrets, restore a backup
- [ ] Rollback tested at least once, deliberately

---

## Definition of done

1. `https://nikunjramani.in` serves the site with a valid certificate
2. `www` redirects to apex
3. `view-source` shows real content
4. Contact form delivers to your inbox
5. Admin login works on the live domain and edits go live within seconds
6. Search Console has the sitemap, with no errors
7. Link previews render correctly on LinkedIn and WhatsApp
8. Production Lighthouse ≥ 95 / 100 / 100
9. Rollback has been tested, not just documented

**🚀 Ship it.**

---

## Gotchas

**GoDaddy parking records are the #1 cause of a stuck domain.** If verification sits pending for
hours, this is almost always why.

**Check DNS with `dig`, not a browser.** Browsers and ISPs cache aggressively; you'll think it's
broken when it propagated twenty minutes ago.

**SSL takes time after verification.** Certificate errors in the first hour are normal. Re-adding
the domain restarts the clock — wait instead.

**Localhost Lighthouse scores lie.** No network latency, no cold cache. Only the production number
counts.

**Secrets differ between emulator and prod.** The first real deploy is where a missing Secret Manager
entry surfaces. Check the function logs immediately after deploying.

**Deploy on a weekday morning.** Not Friday evening. DNS problems take hours to shake out and you
want to be awake for them.

---

**Next:** [Phase 7 · CI/CD Hardening](./phase-7-cicd.md)
