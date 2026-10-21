import type { NextConfig } from "next";

import { API_PREFIX, apiBaseUrl } from "./src/lib/backend";

/**
 * API routing.
 *
 * App Hosting has no `rewrites` of its own (unlike classic Firebase Hosting), so the app does
 * it: the browser only ever talks to this origin, which means no CORS preflight on any API
 * call and cookies work without special handling. The cost is one extra hop through the
 * (already warm) Next server. Server Components skip the hop and call the API directly
 * (lib/data/api.ts).
 *
 * The API is one Cloud Run service serving every /api/v1/<domain>/<sub>/… route (ADR 0023),
 * so one rewrite covers it. The URL scheme lives in src/lib/backend.ts; API_BASE_URL must be
 * set at BUILD time, because Next.js serialises rewrites into the build.
 */

const nextConfig: NextConfig = {
  reactStrictMode: true,

  // The site and the admin are separate root layouts (ADR 0021), so a URL matching neither
  // needs a 404 that brings its own <html>: app/global-not-found.tsx.
  experimental: { globalNotFound: true },

  images: {
    remotePatterns: [
      { protocol: "https", hostname: "storage.googleapis.com" },
      { protocol: "https", hostname: "firebasestorage.googleapis.com" },
    ],
  },

  async rewrites() {
    return [{ source: `${API_PREFIX}/:path*`, destination: `${apiBaseUrl()}${API_PREFIX}/:path*` }];
  },

  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
          ...(process.env.SITE_INDEXABLE === "false"
            ? [{ key: "X-Robots-Tag", value: "noindex, nofollow" }]
            : []),
        ],
      },
    ];
  },
};

export default nextConfig;
