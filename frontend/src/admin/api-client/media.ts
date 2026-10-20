"use client";

/** The backend's media domain: `upload` issues signed URLs, `library` lists, edits and
 * deletes assets (which the processing trigger creates — never a POST body). */
import { apiFetch } from "@/admin/api-client/client";
import type { RecordOut } from "@/admin/api-client/content";
import type { MediaAsset } from "@/generated/types";
import { API_ROUTES } from "@/generated/api-routes";

const LIBRARY = `/${API_ROUTES.media.library}`;

export type MediaRecordOut = RecordOut<MediaAsset>;

export function listMedia(): Promise<MediaRecordOut[]> {
  return apiFetch(`${LIBRARY}/`);
}

export function getMedia(id: string): Promise<MediaRecordOut> {
  return apiFetch(`${LIBRARY}/${encodeURIComponent(id)}`);
}

export function requestUploadUrl(
  contentType: string,
  sizeBytes: number,
): Promise<{ uploadUrl: string; path: string }> {
  return apiFetch(`/${API_ROUTES.media.upload}/`, {
    method: "POST",
    body: JSON.stringify({ contentType, sizeBytes }),
  });
}

export function updateMediaMetadata(
  id: string,
  alt: string,
  caption?: string,
): Promise<MediaRecordOut> {
  return apiFetch(`${LIBRARY}/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify({ alt, caption: caption || undefined }),
  });
}

/** `collection/id` of every content document still pointing at this asset. */
export async function getMediaUsage(id: string): Promise<string[]> {
  const { references } = await apiFetch<{ references: string[] }>(
    `${LIBRARY}/${encodeURIComponent(id)}/usage`,
  );
  return references;
}

/** The API refuses (409) to delete an asset that content still uses unless `force` — set
 * it only after the admin has seen getMediaUsage's list and confirmed. */
export function deleteMedia(id: string, { force = false } = {}): Promise<void> {
  const query = force ? "?force=true" : "";
  return apiFetch(`${LIBRARY}/${encodeURIComponent(id)}${query}`, { method: "DELETE" });
}

/** The signed URL itself is a plain Storage PUT, not a Python API call — no Bearer token,
 * no /api/v1 rewrite, the URL is already fully authorised by its signature. */
export async function uploadToSignedUrl(uploadUrl: string, file: File): Promise<void> {
  const res = await fetch(uploadUrl, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": file.type },
  });
  if (!res.ok) throw new Error(`Upload failed with status ${res.status}`);
}
