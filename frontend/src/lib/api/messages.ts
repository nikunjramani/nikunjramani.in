"use client";

import { apiFetch, apiFetchBlob } from "@/lib/api/client";
import type { RecordOut } from "@/lib/api/content";
import type { ContactMessage } from "@/generated/types";

export type MessageRecordOut = RecordOut<ContactMessage>;

export function listMessages(unreadOnly = false): Promise<MessageRecordOut[]> {
  const qs = unreadOnly ? "?unread_only=true" : "";
  return apiFetch(`/messages/${qs}`);
}

export function getMessage(id: string): Promise<MessageRecordOut> {
  return apiFetch(`/messages/${id}`);
}

export function markMessageRead(id: string): Promise<MessageRecordOut> {
  return apiFetch(`/messages/${id}/read`, { method: "PATCH" });
}

export function markMessageReplied(id: string): Promise<MessageRecordOut> {
  return apiFetch(`/messages/${id}/replied`, { method: "PATCH" });
}

export function deleteMessage(id: string): Promise<void> {
  return apiFetch(`/messages/${id}`, { method: "DELETE" });
}

export async function downloadMessagesCsv(): Promise<void> {
  const blob = await apiFetchBlob("/messages/export.csv");
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "messages.csv";
  a.click();
  URL.revokeObjectURL(url);
}
