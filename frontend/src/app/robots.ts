import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://nikunjramani.in";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // The admin panel (Phase 5) lives under this route group — never meant for an index.
      disallow: ["/admin"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
