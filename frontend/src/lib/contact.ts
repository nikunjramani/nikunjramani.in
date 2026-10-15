"use client";

import { API_ROUTES } from "@/generated/api-routes";

export interface ContactSubmission {
  name: string;
  email: string;
  subject?: string;
  message: string;
  honeypot: string;
  turnstileToken: string;
}

/** Public submission: unlike admin API calls, this intentionally has no Firebase token. */
export async function submitContact(payload: ContactSubmission): Promise<void> {
  const res = await fetch(`/api/v1/${API_ROUTES.inbox.contact}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Contact submission failed with status ${res.status}.`);
}
