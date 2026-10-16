"use client";

import { apiFetch } from "@/admin/api/client";
import type { ContentApiDomain } from "@/generated/api-routes";

export interface RecordOut<T> {
  id: string;
  data: T;
}

/** Collection routes: shared/crud.py's make_crud_router (non-singleton). */
export function listRecords<T>(apiDomain: ContentApiDomain, visibility?: string): Promise<RecordOut<T>[]> {
  const qs = visibility ? `?visibility=${encodeURIComponent(visibility)}` : "";
  return apiFetch(`/${apiDomain}/${qs}`);
}

export function getRecord<T>(apiDomain: ContentApiDomain, id: string): Promise<RecordOut<T>> {
  return apiFetch(`/${apiDomain}/${encodeURIComponent(id)}`);
}

export function createRecord<T>(apiDomain: ContentApiDomain, payload: unknown): Promise<RecordOut<T>> {
  return apiFetch(`/${apiDomain}/`, { method: "POST", body: JSON.stringify(payload) });
}

/** RFC 7386 JSON merge patch — `null` deletes a key. Build it with lib/merge-patch.ts's
 * toMergePatch, never by sending form values directly (a cleared field would be dropped). */
export function patchRecord<T>(
  apiDomain: ContentApiDomain,
  id: string,
  patch: Record<string, unknown>,
): Promise<RecordOut<T>> {
  return apiFetch(`/${apiDomain}/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function deleteRecord(apiDomain: ContentApiDomain, id: string): Promise<void> {
  return apiFetch(`/${apiDomain}/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function reorderRecords(apiDomain: ContentApiDomain, ids: string[]): Promise<void> {
  return apiFetch(`/${apiDomain}/reorder`, { method: "POST", body: JSON.stringify({ ids }) });
}

/** Singleton routes: shared/crud.py's make_crud_router(singleton_id="main") — profile, settings. */
export function getSingleton<T>(apiDomain: ContentApiDomain): Promise<RecordOut<T>> {
  return apiFetch(`/${apiDomain}/`);
}

export function putSingleton<T>(apiDomain: ContentApiDomain, payload: unknown): Promise<RecordOut<T>> {
  return apiFetch(`/${apiDomain}/`, { method: "PUT", body: JSON.stringify(payload) });
}

export function patchSingleton<T>(
  apiDomain: ContentApiDomain,
  patch: Record<string, unknown>,
): Promise<RecordOut<T>> {
  return apiFetch(`/${apiDomain}/`, { method: "PATCH", body: JSON.stringify(patch) });
}
