import "server-only";

// React cache deduplicates reads within a request. Persistent content caching is
// intentionally disabled so publication changes reach every instance (ADR 0014).

import { db } from "@/lib/firebase/admin";

import { fromSnapshot, type WithId } from "./convert";

/** Every content collection filters to visibility == "public" and sorts by `order` —
 * the same convention the backend's admin panel writes. `equals` narrows further (each
 * combination needs its composite index, declared in the schema's x-firestore.indexes). */
export async function listPublished<T>(
  collection: string,
  equals: Record<string, string | boolean> = {},
): Promise<WithId<T>[]> {
  let query = db().collection(collection).where("visibility", "==", "public");
  for (const [field, value] of Object.entries(equals)) {
    query = query.where(field, "==", value);
  }
  const snap = await query.orderBy("order").get();
  return snap.docs.map((doc) => fromSnapshot<T>(doc)).filter((doc): doc is WithId<T> => doc !== null);
}
