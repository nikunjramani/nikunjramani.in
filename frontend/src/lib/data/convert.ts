import "server-only";

import { Timestamp } from "firebase-admin/firestore";
import type { DocumentSnapshot, QueryDocumentSnapshot } from "firebase-admin/firestore";

/**
 * Firestore Timestamp -> ISO string, recursively. Mirrors
 * backend/functions/shared/core/timestamps.py's from_firestore(): the generated types
 * expect plain ISO strings (schemas declare `format: date-time`), but the Admin SDK
 * returns native Timestamp instances on read. This is the one place that conversion
 * happens on the frontend, matching the backend's "exactly one place" rule.
 */
function convert(value: unknown): unknown {
  if (value instanceof Timestamp) {
    return value.toDate().toISOString();
  }
  if (Array.isArray(value)) {
    return value.map(convert);
  }
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([k, v]) => [k, convert(v)]),
    );
  }
  return value;
}

/** A converted document's data, with its Firestore id attached as `id`. The generated
 * schemas never include an `id` field (additionalProperties is false), so it travels
 * alongside the data the same way it does on the backend (shared.repositories.base.Record). */
export type WithId<T> = T & { id: string };

export function fromSnapshot<T>(
  snapshot: DocumentSnapshot | QueryDocumentSnapshot,
): WithId<T> | null {
  if (!snapshot.exists) return null;
  const data = convert(snapshot.data()) as T;
  return { ...data, id: snapshot.id };
}
