import "server-only";

// React cache deduplicates reads within a request. Persistent content caching is
// intentionally disabled so publication changes reach every instance (ADR 0014).

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
