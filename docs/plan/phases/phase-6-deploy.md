# Phase 6 · Deploy & DNS

**~5 hours** · Status: ⬜ Not started · **🚀 LAUNCH**

> **Goal:** nikunjramani.in live on your domain, over HTTPS, indexed by Google,
> with link previews that look right.

---

## Prerequisites

- [ ] Phases 0–5 done
- [ ] [07 · Domain Setup](../07-domain-setup.md) read
- [ ] GoDaddy DNS access to hand

---

## Tasks

### 6.1 · Infrastructure

- [ ] Fill in `modules/functions` — `for_each` over the domain map, per-domain memory and
      `max_instances = 3`, secrets bound
- [ ] Fill in `modules/app-hosting` — backend, GitHub connection, env vars
- [ ] `terraform plan` reviewed
- [ ] `terraform apply`
- [ ] Uptime check and alerts confirmed active

### 6.2 · Backend deploy

- [ ] Secrets populated in Secret Manager (Resend, Turnstile)
- [ ] `firebase deploy --only functions` — confirm **every** domain deployed, none silently skipped
- [ ] Hosting rewrites resolve for every domain — a missing one 404s like a routing bug
- [ ] `/health` responds on the deployed URL, via the rewrite
- [ ] A real contact submission delivers an email
- [ ] Scheduled backup job registered and manually triggered once
- [ ] `/docs` confirmed **disabled** in production

### 6.3 · Frontend deploy

- [ ] `apphosting.yaml` — build command, env vars, runtime config
- [ ] Connect the GitHub repo to App Hosting
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
