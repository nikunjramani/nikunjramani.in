"use client";

const SESSION_ENDPOINT = "/api/admin/session";

export async function createAdminSession(idToken: string): Promise<void> {
  const res = await fetch(SESSION_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idToken }),
  });
  if (!res.ok) throw new Error(`Session exchange failed with status ${res.status}.`);
}

export async function deleteAdminSession(): Promise<void> {
  const res = await fetch(SESSION_ENDPOINT, { method: "DELETE" });
  if (!res.ok) throw new Error(`Session deletion failed with status ${res.status}.`);
}
