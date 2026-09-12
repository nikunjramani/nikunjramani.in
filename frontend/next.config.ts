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
 * Every new domain needs a line here — see ADR 0011.
 */
const FUNCTIONS_BASE =
  process.env.FUNCTIONS_BASE_URL ??
  "http://127.0.0.1:5001/nikunjramani-in/asia-south1";

const DOMAINS = ["system", "contact"] as const;

const nextConfig: NextConfig = {
  reactStrictMode: true,

  images: {
    remotePatterns: [
      { protocol: "https", hostname: "storage.googleapis.com" },
      { protocol: "https", hostname: "firebasestorage.googleapis.com" },
    ],
  },

  async rewrites() {
    return DOMAINS.map((domain) => ({
      source: `/api/v1/${domain}/:path*`,
      destination: `${FUNCTIONS_BASE}/api_${domain}/:path*`,
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
