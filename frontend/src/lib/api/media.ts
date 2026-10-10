"use client";

/** Media doesn't fit shared/crud.py's generic shape — creation happens inside the
 * on_media_uploaded Storage trigger, not a POST body (see src/media/service.py) — so it
 * gets its own small client instead of the generic CRUD helpers in lib/api/content.ts. */
import { apiFetch } from "@/lib/api/client";
import type { MediaAsset } from "@/generated/types";

export interface MediaRecordOut {
  id: string;
  data: MediaAsset;
}

export function listMedia(): Promise<MediaRecordOut[]> {
  return apiFetch("/media/");
}

export function getMedia(id: string): Promise<MediaRecordOut> {
  return apiFetch(`/media/${id}`);
}

export function requestUploadUrl(
  contentType: string,
  sizeBytes: number,
): Promise<{ uploadUrl: string; path: string }> {
  return apiFetch("/media/upload-url", {
    method: "POST",
    body: JSON.stringify({ contentType, sizeBytes }),
  });
}

export function updateMediaMetadata(
  id: string,
  alt: string,
  caption?: string,
): Promise<MediaRecordOut> {
  return apiFetch(`/media/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ alt, caption: caption || undefined }),
  });
}

export function deleteMedia(id: string): Promise<void> {
  return apiFetch(`/media/${id}`, { method: "DELETE" });
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
