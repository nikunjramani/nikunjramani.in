"use client";

/**
 * Firebase App Check for the public contact form (ADR 0020): reCAPTCHA Enterprise scores the
 * visitor invisibly, App Check turns that into a short-lived token, and the contact function
 * verifies it with no secret. The SDK is imported on demand, so it never lands in the bundle of
 * any page that doesn't show the form.
 *
 * NEXT_PUBLIC_RECAPTCHA_SITE_KEY is public by design (like the Firebase config). Unset — local
 * development — means App Check is off and the emulator-backed API skips verification.
 */
import type { AppCheck } from "firebase/app-check";

let instance: Promise<AppCheck | null> | null = null;

/** Starts App Check once. Call it early so reCAPTCHA has signals to score by submit time. */
export function initAppCheck(): Promise<AppCheck | null> {
  const siteKey = process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY;
  if (!siteKey) return Promise.resolve(null);

  instance ??= (async () => {
    const [{ initializeAppCheck, ReCaptchaEnterpriseProvider }, { firebaseApp }] =
      await Promise.all([import("firebase/app-check"), import("@/lib/firebase/client")]);
    return initializeAppCheck(firebaseApp(), {
      provider: new ReCaptchaEnterpriseProvider(siteKey),
      isTokenAutoRefreshEnabled: true,
    });
  })();
  return instance;
}

/** A current App Check token, or "" when App Check isn't configured. Throws if attestation
 *  fails, so the form can say so rather than send a submission the API will drop. */
export async function getAppCheckToken(): Promise<string> {
  const appCheck = await initAppCheck();
  if (!appCheck) return "";
  const { getToken } = await import("firebase/app-check");
  return (await getToken(appCheck)).token;
}
