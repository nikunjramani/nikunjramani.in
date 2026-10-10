# 07 · Domain Setup

`nikunjramani.in`, registered at GoDaddy → pointed at Firebase App Hosting.
Done in [Phase 6](./phases/phase-6-deploy.md).

---

## Steps

### 1 · Add the domain in Firebase

Firebase Console → App Hosting → your backend → **Add custom domain**.
Add `nikunjramani.in` first, then repeat for `www.nikunjramani.in` — **as its own
domain, not a redirect alias.** Firebase gives each one its own TXT ownership claim
and its own A record; it does not hand you a single pair to split between two hosts.

> ⚠️ **Use exactly what the console (or the live domains API) shows you for *this*
> project.** Firebase's hosting IPs and claim strings are per-backend, not universal —
> copying either from a blog post, an old run, or the other host produces a domain
> that never leaves `OWNERSHIP_MISSING`.

### 2 · GoDaddy DNS

GoDaddy → My Products → `nikunjramani.in` → **DNS** → Manage Zones.

| Type | Name | Value | TTL |
|---|---|---|---|
| A | `@` | *(apex A record from Firebase)* | 600 |
| TXT | `@` | *(apex ownership claim from Firebase)* | 600 |
| A | `www` | *(usually the same A record as apex)* | 600 |
| TXT | `www` | *(www's own ownership claim — different from apex's)* | 600 |
| CNAME | `_acme-challenge_<id>` | *(cert validation target from Firebase)* | 3600 |

**Not** a `CNAME www → nikunjramani.in`. The original version of this doc assumed
that was fine — it isn't: a CNAME can't coexist with the A/TXT records `www` also
needs, so it blocks both host and ownership verification for `www` specifically.
Redirecting `www` to the apex is configured in Firebase (`serve.redirect` on the
`www` domain resource), not via a DNS-level CNAME.

### 3 · Delete GoDaddy's defaults ⚠️

GoDaddy pre-populates parking records that **will** conflict:

- [ ] Delete the default `A @ → ` parking IP (usually `Parked` / `WebsiteBuilder`)
- [ ] Delete any default `CNAME www → ` if present
- [ ] Turn off **Domain Forwarding** if it's on

This is the single most common reason a Firebase custom domain sits in "pending" forever.

> **GoDaddy quirk, confirmed live:** editing one record on a host can silently clear
> *every* record on that same host row, not just the one you changed. After any edit,
> re-check the *other* records on that host (`dig <host> A`, `dig <host> TXT`, …) —
> don't assume only the field you touched changed. A `TXT` claim ending up duplicated
> across two different hosts (apex and `www` both carrying the same claim, or vice
> versa) also blocks verification — Firebase requires exactly one ownership claim per
> host, each matching that host's own backend domain resource.

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
| `www` stuck on `OWNERSHIP_MISSING`/`CERT_VALIDATING` indefinitely | Still has a `CNAME → apex` instead of its own A+TXT (step 2) |
| "multiple, conflicting ownership claims" error from Firebase | The same TXT claim (or the other host's claim) duplicated onto this host — each host gets exactly one, its own |
| A record edit "didn't fully apply" | GoDaddy cleared the whole host row, not just the field you edited — re-check every record type on that host |
| Works on `www`, not apex | Missing or wrong A records |
| SSL warning after it goes live | Cert still provisioning — wait, don't re-add the domain |
| Contact emails land in spam | SPF/DKIM missing for Resend |
| Site loads but shows the old parking page | Browser or ISP DNS cache; check with `dig` against the authoritative nameserver (`dig @ns1.yourregistrar.com ...`), not your own resolver or a browser — intermediate caches (including Firebase's own verification resolver) can lag behind the authoritative zone by its old TTL |

---

**Back to:** [Plan index](./README.md)
