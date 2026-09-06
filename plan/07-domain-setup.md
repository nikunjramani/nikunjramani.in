# 07 · Domain Setup

`nikunjramani.in`, registered at GoDaddy → pointed at Firebase App Hosting.
Done in [Phase 6](./phases/phase-6-deploy.md).

---

## Steps

### 1 · Add the domain in Firebase

Firebase Console → App Hosting → your backend → **Add custom domain**.
Add `nikunjramani.in` first, then repeat for `www.nikunjramani.in`.

Firebase gives you a **TXT** record for ownership verification and **two A records**.

> ⚠️ **Use exactly what the console shows you.** Firebase's hosting IPs have changed over the years
> and vary by project. IPs copied from a blog post will produce a site that works today and breaks
> silently later.

### 2 · GoDaddy DNS

GoDaddy → My Products → `nikunjramani.in` → **DNS** → Manage Zones.

| Type | Name | Value | TTL |
|---|---|---|---|
| TXT | `@` | *(verification string from Firebase)* | 600 |
| A | `@` | *(Firebase IP #1)* | 600 |
| A | `@` | *(Firebase IP #2)* | 600 |
| CNAME | `www` | `nikunjramani.in` | 600 |

### 3 · Delete GoDaddy's defaults ⚠️

GoDaddy pre-populates parking records that **will** conflict:

- [ ] Delete the default `A @ → ` parking IP (usually `Parked` / `WebsiteBuilder`)
- [ ] Delete the default `CNAME www → ` if it points anywhere but your domain
- [ ] Turn off **Domain Forwarding** if it's on

This is the single most common reason a Firebase custom domain sits in "pending" forever.

### 4 · Point the API subdomain

| Type | Name | Value |
|---|---|---|
| CNAME | `api` | *(target from the Cloud Run domain mapping)* |

Optional — the API is reachable at its default URL. A clean `api.nikunjramani.in` is nicer to work
with and means the URL doesn't change if the backend moves.

### 5 · Wait

- Verification: usually minutes
- Propagation: usually under an hour, allow up to 48
- SSL: Firebase provisions and renews automatically, no action needed

Check progress:

```bash
dig nikunjramani.in +short
dig www.nikunjramani.in +short
curl -sI https://nikunjramani.in | head -1
```

---

## Redirect policy

Pick one canonical host and 301 the other. Recommendation: **apex** (`nikunjramani.in`) as canonical,
`www` redirects to it. Shorter, and it's what you'd say out loud.

Set the canonical URL in Next.js metadata to match, so search engines don't index both.

---

## Email — optional

For `hello@nikunjramani.in`:

| Option | Cost | Notes |
|---|---|---|
| **Cloudflare Email Routing** | Free | Forwards to Gmail. Receive only, can't send *from* the address |
| **Zoho Mail** | Free tier | Real mailbox, send and receive |
| Google Workspace | Paid | Overkill here |

Recommendation: **Zoho free tier** if you want to actually reply from the address — which you do, if
it's on your CV. Both need MX records added at GoDaddy.

Remember to add **SPF** and **DKIM** records for whichever you pick, or your mail lands in spam.
Resend (used for the contact form) also wants a verified sending domain — same DNS panel, do them
together.

---

## Gotchas

| Symptom | Cause |
|---|---|
| Domain stuck "pending" for hours | GoDaddy parking records not deleted (step 3) |
| Works on `www`, not apex | Missing or wrong A records |
| SSL warning after it goes live | Cert still provisioning — wait, don't re-add the domain |
| Contact emails land in spam | SPF/DKIM missing for Resend |
| Site loads but shows the old parking page | Browser or ISP DNS cache; check with `dig`, not the browser |

---

**Next:** [08 · Costs & Risks](./08-costs-and-risks.md)
