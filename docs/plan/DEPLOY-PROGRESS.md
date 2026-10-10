# Deploy progress — 2026-10-10

Phase 6 is in progress. The application is deployed and usable at
https://nikunjramani-in--nikunjramani-in.asia-southeast1.hosted.app.
DNS cutover is partially applied: apex resolves to Firebase plus two extra addresses;
www still uses the old CNAME, and the ACME CNAME is missing. Do not restart infrastructure setup
or reconnect GitHub to unblock deployment: local-source deployment works (ADR 0013).

## Completed

- Terraform infrastructure applied: budget, IAM, Firestore, storage, secrets,
  App Hosting, domains, uptime check and error/uptime alert policies.
- Twelve HTTP functions, two event triggers and scheduled backup deployed in Mumbai
  under the dedicated functions runtime identity. Secret bindings, event delivery IAM
  and signed-upload permissions corrected and verified.
- App Hosting deployed in Singapore with Node 22, scale to zero, maximum three
  instances, production rewrites and runtime secrets. GitHub connection is optional.
- Firebase Auth initialized, Google provider enabled, production hostnames authorized.
  Owner signed in and received the admin claim; sign out/in to refresh the token.
- Live session cookie/admin route, anonymous API rejection, disabled API docs,
  authenticated revalidation, public routes and private-secret exclusion checked.
- Signed media upload and image trigger verified: WebP, thumbnail and blurhash produced;
  public derivatives accessible. Public storage access is limited to `public/`.
- Scheduled backup invoked successfully; eleven collection JSON exports verified in
  the private backup bucket. These are application JSON, not native Firestore exports.
- Backend: 134 tests passed, 89% coverage; lint, typing, import boundaries and schema
  checks passed. Frontend typing/lint passed (one existing React Hook Form warning).
- Final production Lighthouse after cache fix: 99 performance / 100 accessibility /
  100 SEO on the hosted homepage. Real-content/custom-domain launch still needs review.
- Found and fixed public profile/settings visibility filtering. Found cached-404
  publication failure; request-scoped rendering fix documented in ADR 0014.

- Cache-fix build `build-2026-10-10-004` passed immediate publish/edit/unpublish and
  sitemap checks. Rollback to build 003 and restoration to 004 both passed health checks.
- Temporary smoke Auth user, local ID token, project documents and live media objects
  removed after verification. Audit entries and versioned-object history are retained.
- Media deletion now attempts removal of original, processed image and thumbnail;
  twelve media tests, lint and typing passed. Live delete returned 204 and left zero
  live objects in the smoke upload folder, including when the original was already gone.

## Remaining launch work

1. Verify the owner’s refreshed Google session in the admin UI. Automated admin
   session checks passed; sign out/in after the admin claim grant.
2. Registrar DNS: owner must apply [the exact cutover records](./DNS-CUTOVER.md).
   Then verify ownership, certificate, apex HTTPS and www → apex redirect. The live
   App Hosting API requests A + TXT for www; do not use the old plan's www CNAME.
3. Owner supplies actual profile, projects and résumé through the admin panel.
   Sample smoke content must not remain published.
4. Resend and Turnstile were deliberately deferred. Add keys **and** the corresponding
   Firebase function secret bindings, redeploy, then test a real contact email and spam
   verification. Merely adding secret versions does not bind them to a function.
5. Verify alert email delivery, real-device mobile layout, résumé,
   Search Console sitemap submission and real social previews after domain/content.
6. Phase 7 GitHub Actions/WIF deployment and optional GitHub App Hosting integration
   remain separate work; no automatic rollout is configured by this manual deployment.

## Operational notes

See [RUNBOOK](../RUNBOOK.md) for deploy, rollback, secret rotation and backup restoration.
`frontend/apphosting.yaml` is the app-root configuration; root `apphosting.yaml` is
unused. The backend revalidation URL uses the working hosted domain, independent of
DNS cutover. Keep `.firebase/`, local credentials, Terraform variables/state and log
artifacts private and uncommitted. ₹100/month is an alert threshold, not a spending cap.
