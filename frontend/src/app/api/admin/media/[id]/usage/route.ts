import "server-only";

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { getAdminSession, isAdmin } from "@/lib/auth/session";
import { findMediaUsage } from "@/lib/data/media-usage";

/** GET — which content documents still use this media asset. Checked by the admin media
 * library before a delete. Session-cookie authorised (same origin as the admin panel). */
export async function GET(_req: NextRequest, ctx: RouteContext<"/api/admin/media/[id]/usage">) {
  const claims = await getAdminSession();
  if (!claims) return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  if (!isAdmin(claims)) return NextResponse.json({ error: "forbidden" }, { status: 403 });

  const { id } = await ctx.params;
  const references = await findMediaUsage(id);
  if (references === null) return NextResponse.json({ error: "not found" }, { status: 404 });
  return NextResponse.json({ references });
}
