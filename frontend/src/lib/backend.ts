/**
 * Where the Python API lives — the one place its URL scheme is spelled out. Route names
 * (`content/projects`, …) come from architecture/api-routes.json via generated/api-routes.
 *
 * - The browser calls `${API_PREFIX}/<route>/…` on this origin; next.config.ts rewrites
 *   that to the route's function (ADR 0017).
 * - Server code (lib/data) calls the function directly at `functionUrl(route)` — one hop
 *   fewer than going through its own rewrite.
 *
 * Imported by next.config.ts, so: relative imports only, no `server-only`.
 */
export const API_PREFIX = "/api/v1";

/** `content/projects` → `api_content_projects`, the deployed function's name. */
export function functionName(route: string): string {
  return `api_${route.replace("/", "_")}`;
}

/** The Cloud Functions base URL — the emulator's unless FUNCTIONS_BASE_URL is set
 * (frontend/apphosting*.yaml, for BUILD and RUNTIME). */
export function functionsBaseUrl(): string {
  return process.env.FUNCTIONS_BASE_URL ?? "http://127.0.0.1:5001/nikunjramani-in/asia-south1";
}

export function functionUrl(route: string): string {
  return `${functionsBaseUrl()}/${functionName(route)}`;
}
