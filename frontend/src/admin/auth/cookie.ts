/**
 * The admin session cookie's name and lifetime — one definition for the three places that
 * touch it: proxy.ts (presence check), auth/server.ts (verification) and the session route
 * handler (mint and clear). No imports, so the proxy can use it without pulling in the
 * Admin SDK.
 */
export const SESSION_COOKIE = "session";

/** 5 days — Firebase's own maximum for a session cookie is 2 weeks. */
export const SESSION_MAX_AGE_MS = 5 * 24 * 60 * 60 * 1000;
