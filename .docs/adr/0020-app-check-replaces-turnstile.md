# 0020 · Firebase App Check replaces Cloudflare Turnstile on the contact form

**Status:** ✅ Accepted · **Date:** 2026-10-16
**Deciders:** Owner

---

## Context

The contact form is the one place an anonymous visitor causes a Firestore write and an email.
Its defences are a honeypot, a human/bot check, and rate limits (3 per IP and 20 globally per
hour). The human/bot check must run *before* the rate limiter: without it, a `curl` loop can
exhaust the global window and silently drop every real visitor's message for the rest of the
hour (`src/inbox/contact/service.py`).

That check was Cloudflare Turnstile. It brought a second vendor and a secret
(`TURNSTILE_SECRET_KEY`) to create, store per project, bind to the function, and rotate — and it
blocked the first production deploy, because `firebase deploy` refuses a function whose bound
secret has no version. The owner wanted the third party and the secret gone, without losing the
protection.

## Decision

Use Firebase App Check with a score-based (invisible) reCAPTCHA Enterprise key.

- **Browser:** the contact form initializes App Check on mount (so reCAPTCHA has signals to
  score) and sends a short-lived App Check token in the `X-Firebase-AppCheck` header.
- **Function:** `firebase_admin.app_check.verify_token` checks the token's signature against
  Google's public keys and its audience against this project — locally, with no secret and no
  extra IAM. Missing or invalid tokens are rejected silently in production, exactly where the
  Turnstile check was; development (emulators, no key) skips the check.
- **Terraform** (`modules/app-check`): one reCAPTCHA Enterprise key per project, restricted to
  that project's site domains, registered as the web app's App Check provider. Its site key is
  public and lives in `apphosting*.yaml` as `NEXT_PUBLIC_RECAPTCHA_SITE_KEY`.

## Consequences

### What this makes easier

- No secret to create, store, bind, rotate, or forget before a deploy; the contact function
  binds none.
- One vendor fewer: everything is in the Google project, managed by Terraform.
- Staging and prod each get their own key from the same module, so previews exercise the real
  mechanism instead of a "test always passes" key.

### What this makes harder — the cost we're accepting

- **Google's reCAPTCHA script and badge on the contact page**, and the Firebase client SDK in
  that page's JavaScript (imported on demand, so no other page carries it).
- **Score-based, not challenge-based.** A low score can't be appealed by solving a puzzle; the
  visitor just gets the same silent "thanks". Acceptable for a low-volume personal form.
- **Free-tier limits** on reCAPTCHA Enterprise assessments and App Check exist; a spam wave
  well beyond a personal site's volume would hit them.
- **Local development has no protection** — the same as before.

## Alternatives considered

### Keep Turnstile
Least work, but keeps the secret and the second vendor the owner wanted rid of.

### Remove the human/bot check, keep honeypot + rate limits
Lets anyone jam the global rate limit with a script and silently block real visitors — the
failure the check exists to prevent.

## Revisit if

- Real visitors report messages not arriving (scores too strict for some browsers/networks).
- Spam volume approaches the free-tier limits.
