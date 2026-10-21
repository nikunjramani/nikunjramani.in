/**
 * Where the Python API lives — the one place its URL scheme is spelled out. It is one Cloud
 * Run service (ADR 0023); route names (`content/projects`, …) come from
 * architecture/api-routes.json via generated/api-routes.
 *
 * - The browser calls `${API_PREFIX}/<route>/…` on this origin; next.config.ts rewrites
 *   `${API_PREFIX}/*` to the same path on the API.
 * - Server code (lib/data) calls the API directly at `apiUrl(route)` — one hop fewer than
 *   going through its own rewrite.
 *
 * Imported by next.config.ts, so: relative imports only, no `server-only`.
 */
export const API_PREFIX = "/api/v1";

/** The API's base URL — `make dev-backend` locally unless API_BASE_URL is set
 * (frontend/apphosting*.yaml, for BUILD and RUNTIME). */
export function apiBaseUrl(): string {
  return process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
}

/** `content/projects` → `<API>/api/v1/content/projects`. */
export function apiUrl(route: string): string {
  return `${apiBaseUrl()}${API_PREFIX}/${route}`;
}
