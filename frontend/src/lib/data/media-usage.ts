import "server-only";

import { ADMIN_SCHEMAS } from "@/generated/admin-schemas";
import { db } from "@/lib/firebase/admin";

/** Every content collection the admin panel edits — taken from the generated schemas, so a
 * new content collection is scanned without anyone remembering to add it here. */
const CONTENT_COLLECTIONS = [...new Set(Object.values(ADMIN_SCHEMAS).map((e) => e.collection))];

/**
 * `collection/id` of every content document — drafts included — that mentions the media
 * asset's URL or thumbnail URL anywhere in its data.
 *
 * Lives here rather than in the backend's media domain: it reads other domains' data, and
 * reads belong to Next.js (ADR 0005, ADR 0017). A full scan is fine at this size — tens of
 * documents — and can't drift the way a maintained reference count did. Admin-only: the
 * route calling it checks the session first.
 *
 * Returns null when the asset doesn't exist.
 */
export async function findMediaUsage(assetId: string): Promise<string[] | null> {
  const asset = await db().collection("media_assets").doc(assetId).get();
  if (!asset.exists) return null;

  const data = asset.data() ?? {};
  const urls = new Set(
    [data.url, data.thumbnailUrl].filter((u): u is string => typeof u === "string" && u !== ""),
  );

  const snapshots = await Promise.all(CONTENT_COLLECTIONS.map((c) => db().collection(c).get()));
  return snapshots.flatMap((snap, i) =>
    snap.docs.filter((doc) => mentions(doc.data(), urls)).map((doc) => `${CONTENT_COLLECTIONS[i]}/${doc.id}`),
  );
}

function mentions(value: unknown, urls: Set<string>): boolean {
  if (typeof value === "string") return urls.has(value);
  if (Array.isArray(value)) return value.some((v) => mentions(v, urls));
  if (value !== null && typeof value === "object") {
    return Object.values(value as Record<string, unknown>).some((v) => mentions(v, urls));
  }
  return false;
}
