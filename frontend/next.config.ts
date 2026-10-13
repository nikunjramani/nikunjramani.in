import type { NextConfig } from "next";

/**
 * API routing.
 *
 * The plan originally assumed Firebase Hosting rewrites would unify the per-domain
 * function URLs (ADR 0011). They will not: App Hosting is a separate product from classic
 * Firebase Hosting and has no `rewrites` support — it serves the Next.js backend through a
 * load balancer, and any routing to Functions has to happen in the app itself.
 *
 * So Next.js rewrites do the job instead. This is arguably better: the browser only ever
 * talks to one origin, which means no CORS preflight on any API call and cookies work
 * without special handling. The cost is one extra hop through the (already warm) Next
 * server. Fine for a write-only path used by one admin and the occasional contact form.
 *
 * Each backend subdomain is its own function: /api/v1/<domain>/<sub>/... is rewritten to
 * api_<domain>_<sub> (ADR 0017). Every new subdomain needs a line in ROUTES —
 * backend/functions/tests/test_domain_registry.py fails until it has one.
 */
const FUNCTIONS_BASE =
  process.env.FUNCTIONS_BASE_URL ??
  "http://127.0.0.1:5001/nikunjramani-in/asia-south1";

const ROUTES = [
  "content/profile",
  "content/projects",
  "content/skills",
  "content/experience",
  "content/education",
  "content/certifications",
  "content/posts",
  "content/settings",
  "identity/admins",
  "inbox/contact",
  "inbox/messages",
  "media/upload",
  "media/library",
  "ops/health",
  "ops/audit",
] as const;

const nextConfig: NextConfig = {
  reactStrictMode: true,

  images: {
    remotePatterns: [
      { protocol: "https", hostname: "storage.googleapis.com" },
      { protocol: "https", hostname: "firebasestorage.googleapis.com" },
    ],
  },

  async rewrites() {
    return ROUTES.map((route) => ({
      source: `/api/v1/${route}/:path*`,
      destination: `${FUNCTIONS_BASE}/api_${route.replace("/", "_")}/:path*`,
    }));
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
        ],
      },
    ];
  },
};

export default nextConfig;
