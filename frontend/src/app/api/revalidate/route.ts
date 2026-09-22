import "server-only";

import { revalidateTag } from "next/cache";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Called by shared/services/revalidate.py after every content write. Token-protected: a
 * cache-bust endpoint that anyone could hit would let an outsider force-refresh Firestore
 * reads on demand, which is a cheap way to run up cost for no benefit to them — the shared
 * secret is what stops that, not obscurity of the URL.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
  const expected = process.env.REVALIDATE_TOKEN;
  const provided = request.headers.get("authorization")?.replace(/^Bearer /, "");

  if (!expected || provided !== expected) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const body = (await request.json().catch(() => null)) as { tags?: unknown } | null;
  const tags = body?.tags;
  if (!Array.isArray(tags) || tags.some((t) => typeof t !== "string")) {
    return NextResponse.json({ error: "expected { tags: string[] }" }, { status: 422 });
  }

  for (const tag of tags as string[]) {
    // Next 16 deprecated the single-argument form. "max" is Next's own recommended
    // profile: visitors get stale-while-revalidate (never blocked on a slow read) rather
    // than an immediate hard miss — an admin edit becoming visible within seconds is fine
    // for this site; a visitor never waiting on a blocking Firestore read matters more.
    revalidateTag(tag, "max");
  }

  return NextResponse.json({ revalidated: tags });
}
