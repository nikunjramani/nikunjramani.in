"use client";

/** The backend's media domain: `upload` issues signed URLs, `library` lists, edits and
 * deletes assets (which the processing trigger creates — never a POST body). */
import { ApiError, apiFetch } from "@/admin/api/client";
import type { RecordOut } from "@/admin/api/content";
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

/** `collection/id` of every content document still pointing at this asset. A read across
 * the content collections, so Next.js answers it, not the media domain (ADR 0017) — a
 * same-origin route authorised by the admin session cookie, not the Python API. */
export async function getMediaUsage(id: string): Promise<string[]> {
  const res = await fetch(`/api/admin/media/${encodeURIComponent(id)}/usage`);
  if (!res.ok) throw new ApiError(res.status, "Couldn't check where this image is used.");
  const { references } = (await res.json()) as { references: string[] };
  return references;
}

export function deleteMedia(id: string): Promise<void> {
  return apiFetch(`${LIBRARY}/${encodeURIComponent(id)}`, { method: "DELETE" });
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
