import "server-only";

import { cookies } from "next/headers";
import type { DecodedIdToken } from "firebase-admin/auth";

import { adminAuth } from "@/lib/firebase/admin";

/**
 * The real authorisation check for the admin panel — proxy.ts only checks that a session
 * cookie is present, by design (see its own comment). This is the layer that actually
 * verifies it, in (admin)/admin/(protected)/layout.tsx.
 *
 * Convenience only, same as the plan's own reminder (docs/03-security.md): every write is
 * re-authorised server-side by the Python API regardless of what this returns.
 */
export async function getAdminSession(): Promise<DecodedIdToken | null> {
  const cookie = (await cookies()).get("session")?.value;
  if (!cookie) return null;
  try {
    // checkRevoked: true — a revoked session (sign-out-everywhere, or the admin claim
    // being pulled) stops working immediately rather than staying valid until it expires.
    return await adminAuth().verifySessionCookie(cookie, true);
  } catch {
    return null;
  }
}

export function isAdmin(claims: DecodedIdToken | null): boolean {
  return claims?.admin === true;
}
