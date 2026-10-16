# 0013 · Deploy App Hosting from local source before connecting GitHub

**Status:** ✅ Accepted · **Date:** 2026-10-10

## Context

The Phase 6 plan assumed a GitHub OAuth connection was required to deploy. Firebase
CLI 14.20 supports local-source App Hosting deployments. The owner asked to complete
setup from the existing authenticated workstation without a console OAuth handshake.
The live App Hosting locations API does not offer Mumbai (`asia-south1`).

## Decision

Terraform creates the backend in Singapore (`asia-southeast1`), with an optional
Developer Connect repository. `firebase deploy --only apphosting` uploads the local
source and builds it remotely. `firebase.json` selects `frontend` as the app root,
and `frontend/apphosting.yaml` controls build/runtime configuration. Functions and
Firestore remain in Mumbai. No change to the read/write architecture.

## Consequences

A first deployment no longer waits on GitHub consent or a push. Uncommitted source can
be deployed, so inspect the diff and run checks first. Explicit upload exclusions keep
local env files, Terraform state, credentials and emulator data out of the archive.
Cross-region Firestore reads add latency. GitHub automatic rollouts remain optional
Phase 7 work and require the owner's OAuth consent.

## Alternatives considered

Wait for GitHub consent: unnecessary for the manual launch path. Move the whole stack
to Singapore: unnecessary data migration. Use classic Hosting: loses App Hosting's
managed Next.js build and runtime.

## References

- https://firebase.google.com/docs/app-hosting/alt-deploy
- https://firebase.google.com/docs/app-hosting/configure
