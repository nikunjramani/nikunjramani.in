# Phase 6 · Deploy & DNS

**~5 hours** · Status: 🟡 Deployed & DNS live — 2026-10-10 · a few launch checks remain · **🚀 LAUNCH**

> **Goal:** nikunjramani.in live on your domain, over HTTPS, indexed by Google,
> with link previews that look right.

⛔ **This is the phase that needs Blaze billing.** Everything before it runs on the emulators.
Blaze is enabled. `https://nikunjramani.in` is live with a valid certificate — see
[ADR 0013](../../adr/0013-local-source-app-hosting.md) and
[ADR 0014](../../adr/0014-request-scoped-content-cache.md) for what actually got built,
and [docs/RUNBOOK.md](../../RUNBOOK.md) for operating it.

---

## Prerequisites

- [ ] Phases 0–5 done
- [x] [07 · Domain Setup](../07-domain-setup.md) read
- [ ] GoDaddy DNS access to hand

---

## Tasks

### 6.1 · Infrastructure

- [x] Terraform IAM, storage, budget, secrets, Firestore and App Hosting applied.
- [x] App Hosting backend in Singapore; local-source deploy (ADR 0013).
- [x] Function runtime settings and secrets configured in Firebase Python decorators.
- [x] `terraform plan` reviewed and applied.
- [x] Uptime check on `/api/v1/system/health` and error/uptime policies active.
- [ ] Alert notification delivery verified in the owner's inbox.

### 6.2 · Backend deploy

- [ ] Secrets populated in Secret Manager (Resend, Turnstile) — **now blocking**: both are
      bound to the contact functions, so the next functions deploy needs them, and the form
      fails closed in production without Turnstile. See docs/RUNBOOK.md (Contact form keys).
      `CONTACT_EMAIL_TO` is populated; `REVALIDATE_TOKEN` is retired (ADR 0015)
- [x] `firebase deploy --only functions` — all 12 domains + 2 triggers + the scheduled
      backup, confirmed via `firebase functions:list`, none silently skipped
- [x] All twelve production rewrites configured; health and admin routes tested live.
- [x] Rewritten `/api/v1/system/health` responds with production environment.
- [ ] A real contact submission delivers an email — blocked on the deferred Resend key
- [x] Scheduled backup manually triggered on 2026-10-10; HTTP 200 and all 11 JSON exports verified in the private backup bucket.
- [x] `/docs` confirmed **disabled** in production — a real gap, not a formality: the
      first deploy had `/docs` and `/openapi.json` publicly reachable on all 12
      domains because nothing set `ENVIRONMENT=production` at deploy time. Fixed via
      `backend/functions/.env.nikunjramani-in` and reverified — both now 404

### 6.3 · Frontend deploy

- [x] `frontend/apphosting.yaml` — framework build detection, Node 22, build/runtime env, scale to zero, max 3 instances
- [ ] Optional: connect GitHub for automatic rollouts. Manual deployment uses local source (ADR 0013).
- [x] Production build succeeds
- [x] Site reachable on the default App Hosting URL
- [x] Server-side env vars confirmed **not** in the client bundle

### 6.4 · DNS

Real records differed from [07 · Domain Setup](../07-domain-setup.md)'s original plan
in one important way — `www` needs its own A+TXT, not a CNAME to apex — now corrected
in that doc, along with the GoDaddy gotchas hit along the way.

- [x] Custom domain added in Firebase for apex and `www`
- [x] TXT verification record added at GoDaddy (one claim per host, not shared)
- [x] Apex A record added; `www` A record added (its own record, not a CNAME)
- [x] Shared ACME authorization CNAME added
- [x] **GoDaddy parking records and forwarding deleted** ⚠️
- [x] Verification passed on both domains — `OWNERSHIP_ACTIVE` on apex and `www`
      (`www` took longer to reconcile than apex; DNS was confirmed correct on both
      authoritative nameservers throughout — it was Firebase's own async catch-up,
      never a DNS problem)
- [x] SSL provisioned on both — `CERT_ACTIVE`, confirmed via `curl -I` on each host
- [x] `www` → apex redirect confirmed — `https://www.nikunjramani.in` returns
      `301 Location: https://nikunjramani.in/`

### 6.5 · SEO go-live

- [ ] Google Search Console — property verified
- [ ] `sitemap.xml` submitted
- [x] `robots.txt` correct and reachable on hosted URL
- [ ] Rich Results Test passes on the JSON-LD
- [ ] LinkedIn Post Inspector shows the right preview
- [ ] WhatsApp / iMessage previews checked on a phone
- [x] Canonical base configured as `https://nikunjramani.in` (DNS pending)

### 6.6 · Smoke tests

- [x] Static public routes load over HTTPS on hosted URL
- [x] Temporary project detail rendered with real Firestore content (fixture removed)
- [ ] Contact form → email received
- [ ] Résumé download works
- [x] Google sign-in and admin session verified on hosted URL; owner admin claim granted
- [x] Authenticated API publish/edit/unpublish visible immediately; sitemap follows changes (ADR 0014).
- [x] Production hosted homepage Lighthouse after cache fix: 99 / 100 / 100.
- [x] 404 page works
- [ ] Mobile check on a real device

### 6.7 · Runbook

- [x] `docs/RUNBOOK.md` — deploy, rollback, rotate secrets, restore a backup
- [x] App Hosting rollback to build 003 and restoration to build 004 rehearsed; health 200 at each step.

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
