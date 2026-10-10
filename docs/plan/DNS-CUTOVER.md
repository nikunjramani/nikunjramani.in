# Production DNS cutover — 2026-10-10

> Claim/CNAME values below are placeholders. They're not secrets — they're public DNS
> records anyone can already read with `dig` — but there's no reason to pin the exact
> strings in a committed doc either. Get the real current values with `gddy dns list
> nikunjramani.in` or `dig` if you ever need them again.

Firebase App Hosting has both domains registered. `www` is configured to redirect to
`https://nikunjramani.in` with HTTP 301. The working preview is
https://nikunjramani-in--nikunjramani-in.asia-southeast1.hosted.app.

These records came from the live App Hosting domains API, not the original plan.
GoDaddy → My Products → nikunjramani.in → DNS → Manage DNS. Save existing records
before editing. Set TTL to 600 seconds (or the lowest available).

| Type | Name | Value |
|---|---|---|
| A | @ | 35.219.201.46 |
| TXT | @ | <redacted-apex-claim> |
| CNAME | _acme-challenge_hxwqsewlvufusbgf | <redacted-acme-authorization-target> |
| A | www | 35.219.201.46 |
| TXT | www | <redacted-www-claim> |

Replace the existing `A @ → 160.153.0.80` with the A record above. Remove the existing
`CNAME www → nikunjramani.in` before adding `A www` and `TXT www`; a CNAME cannot
coexist with these. Keep unrelated MX, SPF, DKIM and verification records. Disable
GoDaddy domain forwarding if enabled. The shared certificate CNAME is added only once.

This overrides the original plan's assumed two A records and CNAME www-to-apex.
Do not delete or recreate the Firebase domains while waiting for certificate validation.

Verify with `dig nikunjramani.in A +short`, `dig www.nikunjramani.in A +short`,
TXT lookups for both, and the certificate CNAME. Then check HTTPS on both hosts and
confirm a path such as `/about` survives the www-to-apex redirect. Firebase must report
`HOST_ACTIVE`, `OWNERSHIP_ACTIVE`, and `CERT_ACTIVE` before cutover is complete.

## Latest check — 2026-10-10 15:16 IST

Apex A contains the correct Firebase address **plus** `15.197.225.128` and
`3.33.251.168`; remove both extras (disable forwarding if GoDaddy locks them).
The www claim TXT was added at `@`; move that claim to `www`. The www CNAME still
exists and must be replaced by the A/TXT pair above. ACME CNAME is still missing.

## Latest check — 2026-10-10 (dig + live Firebase domains API)

Real progress since the check above:

- ✅ Apex `A @` is now clean — just `35.219.201.46`, the two extra IPs are gone.
- ✅ ACME challenge CNAME now exists and resolves correctly.

Two edits still outstanding — confirmed both by `dig` and by Firebase's own
`backends/nikunjramani-in/domains` API, which currently reports both custom domains
stuck at `OWNERSHIP_MISSING` / `CERT_VALIDATING` with:
`"Custom Domain has multiple, conflicting ownership claims. There must be at most
one TXT record with the hosting-site= prefix on the domain."` (code `CD_CONFLICTING_CLAIMS`)

1. **Apex (`@`) has both TXT claims.** `dig nikunjramani.in TXT +short` shows:
   - `<redacted-apex-claim>` ← the apex claim, **keep**
   - `<redacted-www-claim>` ← the **www** claim,
     wrongly added at apex too — **delete this one TXT record from `@`**

2. **`www` is still `CNAME → nikunjramani.in`**, not its own A+TXT pair. A CNAME can't
   coexist with other records on the same name, which is also why its TXT claim can't
   really land on `www` while the CNAME is there. **Delete the CNAME**, then add on `www`:
   - `A www → 35.219.201.46`
   - `TXT www → <redacted-www-claim>`

Nothing else needs touching — apex A, apex's own TXT claim, and the ACME CNAME are all
already correct. Once both edits land and DNS propagates, Firebase's next recheck
should move both domains to `HOST_ACTIVE` / `OWNERSHIP_ACTIVE`, then `CERT_ACTIVE`
once the cert issues. Re-verify with the same `dig` commands and the domains API
above — don't just trust the console UI's cache.

## DNS cutover complete — 2026-10-10 (verified against authoritative nameservers)

Both edits landed. Verified directly against `ns23.domaincontrol.com` and
`ns24.domaincontrol.com` (not a cached resolver):

- `A @ → 35.219.201.46` ✓
- `TXT @ → <redacted-apex-claim>` ✓ (exactly one claim)
- `A www → 35.219.201.46` ✓, `TXT www → <redacted-www-claim>` ✓, no CNAME ✓
- ACME challenge CNAME ✓

One real scare along the way: right after removing the duplicate TXT claim, a `dig`
against the authoritative nameservers showed apex had **zero** A and TXT records —
the edit apparently cleared the whole `@` host row instead of just the one record.
The bare domain was briefly unresolvable for anyone whose cache had expired. Re-added
both records and reconfirmed. Lesson: after any GoDaddy edit, re-check the *other*
records on the same host row, not just the one you meant to change.

DNS-side work is done. Firebase's `backends/.../domains` API still showed the stale
`CD_CONFLICTING_CLAIMS` issue and `OWNERSHIP_MISSING` right after this fix — that's
its own control plane not having repolled yet, not a sign DNS is wrong. No manual
"verify now" API exists; it polls on its own schedule (typically well under an hour).
Re-check via the same authoritative-nameserver `dig` commands plus the domains API
to confirm it reaches `HOST_ACTIVE` / `OWNERSHIP_ACTIVE` / `CERT_ACTIVE`.
