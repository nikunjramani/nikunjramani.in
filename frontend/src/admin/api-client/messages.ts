"use client";

import { apiFetch, apiFetchBlob } from "@/admin/api-client/client";
import type { RecordOut } from "@/admin/api-client/content";
import type { ContactMessage } from "@/generated/types";
import { API_ROUTES } from "@/generated/api-routes";

const MESSAGES = `/${API_ROUTES.inbox.messages}`;

export type MessageRecordOut = RecordOut<ContactMessage>;

export function listMessages(unreadOnly = false): Promise<MessageRecordOut[]> {
  const qs = unreadOnly ? "?unread_only=true" : "";
  return apiFetch(`${MESSAGES}/${qs}`);
}

export function getMessage(id: string): Promise<MessageRecordOut> {
  return apiFetch(`${MESSAGES}/${encodeURIComponent(id)}`);
}

export function markMessageRead(id: string): Promise<MessageRecordOut> {
  return apiFetch(`${MESSAGES}/${encodeURIComponent(id)}/read`, { method: "PATCH" });
}

export function markMessageReplied(id: string): Promise<MessageRecordOut> {
  return apiFetch(`${MESSAGES}/${encodeURIComponent(id)}/replied`, { method: "PATCH" });
}

export function deleteMessage(id: string): Promise<void> {
  return apiFetch(`${MESSAGES}/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export async function downloadMessagesCsv(): Promise<void> {
  const blob = await apiFetchBlob(`${MESSAGES}/export.csv`);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "messages.csv";
  a.click();
  URL.revokeObjectURL(url);
}
