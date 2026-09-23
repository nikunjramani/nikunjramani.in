"use client";

import { apiFetch } from "@/lib/api/client";

export interface RecordOut<T> {
  id: string;
  data: T;
}

/** Collection routes: shared/crud.py's make_crud_router (non-singleton). */
export function listRecords<T>(apiDomain: string, visibility?: string): Promise<RecordOut<T>[]> {
  const qs = visibility ? `?visibility=${encodeURIComponent(visibility)}` : "";
  return apiFetch(`/${apiDomain}/${qs}`);
}

export function getRecord<T>(apiDomain: string, id: string): Promise<RecordOut<T>> {
  return apiFetch(`/${apiDomain}/${id}`);
}

export function createRecord<T>(apiDomain: string, payload: unknown): Promise<RecordOut<T>> {
  return apiFetch(`/${apiDomain}/`, { method: "POST", body: JSON.stringify(payload) });
}

/** RFC 7386 JSON merge patch — a top-level `null` deletes that key. */
export function patchRecord<T>(
  apiDomain: string,
  id: string,
  patch: Record<string, unknown>,
): Promise<RecordOut<T>> {
  return apiFetch(`/${apiDomain}/${id}`, { method: "PATCH", body: JSON.stringify(patch) });
}

export function deleteRecord(apiDomain: string, id: string): Promise<void> {
  return apiFetch(`/${apiDomain}/${id}`, { method: "DELETE" });
}

export function reorderRecords(apiDomain: string, ids: string[]): Promise<void> {
  return apiFetch(`/${apiDomain}/reorder`, { method: "POST", body: JSON.stringify({ ids }) });
}

/** Singleton routes: shared/crud.py's make_crud_router(singleton_id="main") — profile, settings. */
export function getSingleton<T>(apiDomain: string): Promise<RecordOut<T>> {
  return apiFetch(`/${apiDomain}/`);
}

export function putSingleton<T>(apiDomain: string, payload: unknown): Promise<RecordOut<T>> {
  return apiFetch(`/${apiDomain}/`, { method: "PUT", body: JSON.stringify(payload) });
}

export function patchSingleton<T>(
  apiDomain: string,
  patch: Record<string, unknown>,
): Promise<RecordOut<T>> {
  return apiFetch(`/${apiDomain}/`, { method: "PATCH", body: JSON.stringify(patch) });
}
