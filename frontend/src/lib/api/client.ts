"use client";

/**
 * The admin panel's one path to the Python API. Every call attaches a fresh Firebase ID
 * token — `getIdToken()` returns the cached one when it's still valid and silently
 * refreshes it when it's not, so this is also what "token refresh" (5.1) actually means in
 * practice: there's no separate refresh machinery, just always asking the SDK for a current
 * token right before the request that needs it.
 *
 * Requests go to /api/v1/<domain>/..., which next.config.ts rewrites to the matching Python
 * function — the browser only ever talks to one origin. See ADR 0011.
 */
import { auth } from "@/lib/firebase/client";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function authHeader(): Promise<string> {
  // auth().currentUser is synchronously null for a moment on every fresh page load —
  // restoring a persisted session from IndexedDB is itself async, and a component's first
  // effect can easily fire before it resolves. authStateReady() is the SDK's own signal
  // for "persistence restoration has finished, one way or the other" — without waiting on
  // it, the very first fetch after any full navigation (not just a soft client transition)
  // fails with a false "not signed in", even though the session cookie and the actual
  // Firebase session are both perfectly valid.
  const instance = auth();
  await instance.authStateReady();
  const user = instance.currentUser;
  if (!user) throw new ApiError(401, "Not signed in.");
  return `Bearer ${await user.getIdToken()}`;
}

async function parseErrorMessage(res: Response): Promise<string> {
  const body: unknown = await res.json().catch(() => null);
  if (body && typeof body === "object") {
    // shared/core/errors.py's DomainError shape.
    if ("error" in body && typeof body.error === "object" && body.error && "message" in body.error) {
      const message = (body.error as { message: unknown }).message;
      if (typeof message === "string") return message;
    }
    // FastAPI's own pydantic validation-error shape (a malformed request body, distinct
    // from a validated-but-rejected one, which is the DomainError case above).
    if ("detail" in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
    }
  }
  return `Request failed with status ${res.status}.`;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", await authHeader());
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`/api/v1${path}`, { ...init, headers });

  if (res.status === 401) {
    // The session cookie gating page navigation and the Bearer token gating this call are
    // verified independently — a 401 here means the token itself is bad, which page-level
    // middleware can't have caught. Bouncing to login is the only sane response.
    //
    // A hard navigation, not router.push(): this function is called from plain data
    // helpers with no component context to pull useRouter() from, and a full reload is
    // actually what's wanted here anyway — it clears whatever stale client SDK / component
    // state got the app into this situation in the first place.
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.href = "/admin/login";
    throw new ApiError(401, "Session expired.");
  }
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorMessage(res));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}
