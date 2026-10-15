/** Site identity. SITE_NAME is the fallback shown while profile/main doesn't exist yet. */
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://nikunjramani.in";
export const SITE_NAME = "Nikunj Ramani";
/** False on staging (apphosting.staging.yaml) — a preview must never be indexed. */
export const SITE_INDEXABLE = process.env.SITE_INDEXABLE !== "false";
