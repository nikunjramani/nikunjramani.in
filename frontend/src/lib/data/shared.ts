import "server-only";

// Uses `unstable_cache` throughout this data layer, not Next 16's newer `'use cache'`
// directive + Cache Components. Cache Components is opt-in via the `cacheComponents` flag
// in next.config.ts, which this project does not set — so `unstable_cache` is the current,
// fully-supported "Previous Model" API, not a deprecated one in practice, even though its
// own doc comment points at the newer directive as the longer-term direction. Worth
// revisiting once Cache Components is more battle-tested; not a blocker for Phase 4.

import { db } from "@/lib/firebase/admin";

import { fromSnapshot, type WithId } from "./convert";

/** Every content collection filters to visibility == "public" and sorts by `order` —
 * the same convention the backend's admin panel writes, so a published document appears
 * here without any extra query logic per collection. */
export async function listPublished<T>(collection: string): Promise<WithId<T>[]> {
  const snap = await db()
    .collection(collection)
    .where("visibility", "==", "public")
    .orderBy("order")
    .get();
  return snap.docs.map((doc) => fromSnapshot<T>(doc)).filter((doc): doc is WithId<T> => doc !== null);
}

export async function getPublishedBySlug<T>(
  collection: string,
  slug: string,
): Promise<WithId<T> | null> {
  const snap = await db().collection(collection).doc(slug).get();
  const doc = fromSnapshot<T>(snap);
  // A visitor guessing a draft's slug must see a 404, not a preview of unpublished work.
  if (!doc || (doc as { visibility?: string }).visibility !== "public") return null;
  return doc;
}
