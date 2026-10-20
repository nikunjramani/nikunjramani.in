"use client";

import { API_ROUTES } from "@/generated/api-routes";
import { API_PREFIX } from "@/lib/backend";

export interface ContactSubmission {
  name: string;
  email: string;
  subject?: string;
  message: string;
  honeypot: string;
}

/**
 * Public submission: no Firebase Auth token, but an App Check token proving it came from this
 * site (ADR 0020). Empty only where App Check isn't configured (local dev); production rejects
 * a submission without one.
 */
export async function submitContact(
  payload: ContactSubmission,
  appCheckToken: string,
): Promise<void> {
  const res = await fetch(`${API_PREFIX}/${API_ROUTES.inbox.contact}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(appCheckToken ? { "X-Firebase-AppCheck": appCheckToken } : {}),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Contact submission failed with status ${res.status}.`);
}
