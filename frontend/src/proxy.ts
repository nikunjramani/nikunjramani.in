import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Presence check only, even though Proxy defaults to the Node.js runtime as of Next 16 and
 * could run the real Firebase session-cookie verification here. Keeping this as a cheap
 * presence check and doing the actual cryptographic check in
 * (admin)/admin/(protected)/layout.tsx is a deliberate two-layer design, not a runtime
 * limitation worked around: a logged-out visitor never even reaches the layout (fast,
 * no crypto), and the layout's own verifySessionCookie call is what an attacker with a
 * forged cookie actually has to get past — proxy alone was never meant to be that gate,
 * see the Node.js Migration guide's own warning: "Always verify authentication and
 * authorization inside each Server Function rather than relying on Proxy alone."
 */
export function proxy(request: NextRequest): NextResponse {
  const hasSession = request.cookies.has("session");
  if (!hasSession) {
    const loginUrl = new URL("/admin/login", request.url);
    return NextResponse.redirect(loginUrl);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/((?!login).*)"],
};
