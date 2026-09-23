import "server-only";

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { adminAuth } from "@/lib/firebase/admin";

const SESSION_COOKIE = "session";
const EXPIRES_IN_MS = 5 * 24 * 60 * 60 * 1000; // 5 days — Firebase's own max is 2 weeks

/**
 * Exchanges a fresh Firebase ID token (proof the browser just completed Google sign-in)
 * for a long-lived, httpOnly session cookie. The ID token itself is never stored client
 * side past this call — it's short-lived and awkward to keep fresh across page loads,
 * where a session cookie is exactly what it's designed for. Every actual write still goes
 * through the Python API with its own freshly-fetched Bearer token (see lib/api/client.ts);
 * this cookie only gates admin page navigation.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  const body = (await request.json().catch(() => null)) as { idToken?: unknown } | null;
  const idToken = body?.idToken;
  if (typeof idToken !== "string" || !idToken) {
    return NextResponse.json({ error: "expected { idToken: string }" }, { status: 422 });
  }

  try {
    // checkRevoked-equivalent at mint time: createSessionCookie itself verifies the ID
    // token first, so an expired or tampered token never becomes a valid cookie.
    const cookie = await adminAuth().createSessionCookie(idToken, { expiresIn: EXPIRES_IN_MS });
    const response = NextResponse.json({ ok: true });
    response.cookies.set(SESSION_COOKIE, cookie, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: EXPIRES_IN_MS / 1000,
    });
    return response;
  } catch {
    return NextResponse.json({ error: "invalid or expired token" }, { status: 401 });
  }
}

export async function DELETE(): Promise<NextResponse> {
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(SESSION_COOKIE);
  return response;
}
