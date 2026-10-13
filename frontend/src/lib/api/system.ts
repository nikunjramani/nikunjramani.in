"use client";

import { apiFetch } from "@/lib/api/client";

export interface AuditEntry {
  id: string;
  actor: string;
  actorEmail?: string;
  action: string;
  collection: string;
  docId?: string;
  at: string;
}

/** GET /system/audit-log — newest first, optionally narrowed to one collection/document. */
export function listAuditLog(filter: { collection?: string; docId?: string; limit?: number } = {}) {
  const params = new URLSearchParams();
  if (filter.collection) params.set("collection", filter.collection);
  if (filter.docId) params.set("docId", filter.docId);
  if (filter.limit) params.set("limit", String(filter.limit));
  const qs = params.toString();
  return apiFetch<AuditEntry[]>(`/system/audit-log${qs ? `?${qs}` : ""}`);
}
