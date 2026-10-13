"use client";

import { apiFetch } from "@/lib/api/client";

export interface Admin {
  uid: string;
  email: string | null;
  displayName: string | null;
}

/** The backend's identity/admins subdomain — who holds the `admin` custom claim. */
export function listAdmins(): Promise<Admin[]> {
  return apiFetch("/identity/admins/");
}

/** The user must have signed in to the site once, so the account exists. Takes effect on
 * their next sign-in (a claim only lands in a freshly issued token). */
export function grantAdmin(email: string): Promise<Admin> {
  return apiFetch("/identity/admins/", { method: "POST", body: JSON.stringify({ email }) });
}

/** Also signs them out everywhere. Refused for yourself and for the last admin. */
export function revokeAdmin(uid: string): Promise<void> {
  return apiFetch(`/identity/admins/${encodeURIComponent(uid)}`, { method: "DELETE" });
}
