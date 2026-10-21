import "server-only";

import { apiUrl } from "@/lib/backend";

/**
 * The public site's only way to its data: the Python API's unauthenticated `/public`
 * routes (ADR 0022). The API applies visibility, strips confidential fields and the audit
 * block, and converts timestamps — nothing here knows Firestore exists.
 *
 * `cache: "no-store"`: content renders per request so a publish or unpublish shows up on
 * the next load (ADR 0014). React `cache` in each lib/data module dedupes within a render.
 */

/** A document with its id alongside — the generated schemas never include an `id`. */
export type WithId<T> = T & { id: string };

interface RecordOut<T> {
  id: string;
  data: T;
}

const withId = <T>({ id, data }: RecordOut<T>): WithId<T> => ({ ...data, id });

async function request(route: string, path: string): Promise<Response | null> {
  const res = await fetch(`${apiUrl(route)}/public${path}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`GET ${route}/public${path} failed with status ${res.status}`);
  return res;
}

/** Every `public` document of a collection, in `order`. */
export async function listPublic<T>(route: string): Promise<WithId<T>[]> {
  const res = await request(route, "");
  return res ? ((await res.json()) as RecordOut<T>[]).map(withId) : [];
}

/** One document (`id`), or a singleton (no `id`); null when the API says 404. */
export async function getPublic<T>(route: string, id?: string): Promise<WithId<T> | null> {
  const res = await request(route, id ? `/${encodeURIComponent(id)}` : "");
  return res ? withId((await res.json()) as RecordOut<T>) : null;
}
