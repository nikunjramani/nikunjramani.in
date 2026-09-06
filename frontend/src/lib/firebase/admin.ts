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

  // In Cloud Run / App Hosting, credentials are ambient — no key file exists anywhere.
  const raw = process.env.FIREBASE_SERVICE_ACCOUNT;
  return initializeApp(raw ? { credential: cert(JSON.parse(raw)) } : {});
}

export function db(): Firestore {
  return getFirestore(app());
}
