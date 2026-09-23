"use client";

/**
 * Firebase client SDK — used only for Auth in the admin panel.
 *
 * These NEXT_PUBLIC_ values are public by design. They identify the project; they do not
 * authorise anything. The security is in the Firestore rules, not in hiding this config.
 *
 * Note there is no Firestore client here on purpose: clients never read or write Firestore
 * directly. Reads happen server-side (ADR 0005), writes go through the API (ADR 0007).
 */
import { getApp, getApps, initializeApp } from "firebase/app";
import { connectAuthEmulator, getAuth, type Auth } from "firebase/auth";

const config = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

let connectedToEmulator = false;

export function auth(): Auth {
  const isNewApp = !getApps().length;
  const instance = getAuth(isNewApp ? initializeApp(config) : getApp());

  const emulatorHost = process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST;
  if (emulatorHost && !connectedToEmulator) {
    connectAuthEmulator(instance, `http://${emulatorHost}`, { disableWarnings: true });
    connectedToEmulator = true;
  }

  return instance;
}
