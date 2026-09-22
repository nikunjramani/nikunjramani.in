import "server-only";

/**
 * Firebase Admin SDK — server-side only.
 *
 * The `server-only` import above is load-bearing: without it, an accidental import from a
 * Client Component leaks admin credentials into the browser bundle. With it, that mistake
 * is a build error instead.
 *
 * Reads go through here, never through the Python API — see ADR 0005.
 */
import { cert, getApps, initializeApp, type App } from "firebase-admin/app";
import { getFirestore, type Firestore } from "firebase-admin/firestore";

function app(): App {
  const existing = getApps();
  if (existing.length) return existing[0];

  // projectId has to be explicit: without a service account, the SDK has nothing else to
  // infer it from, and the Firestore emulator namespaces its data by project id too (the
  // backend sets the equivalent GOOGLE_CLOUD_PROJECT for the same reason).
  const projectId = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID ?? "nikunjramani-in";

  // In Cloud Run / App Hosting, credentials are ambient — no key file exists anywhere.
  const raw = process.env.FIREBASE_SERVICE_ACCOUNT;
  return initializeApp(raw ? { credential: cert(JSON.parse(raw)), projectId } : { projectId });
}

export function db(): Firestore {
  return getFirestore(app());
}
