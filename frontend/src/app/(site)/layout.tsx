// Content changes must reach visitors without a stale CDN response (ADR 0014).
export const revalidate = 0;

import type { ReactNode } from "react";

import { Footer } from "@/components/site/footer";
import { JsonLd } from "@/components/site/json-ld";
import { Nav } from "@/components/site/nav";
import { getProfile } from "@/lib/data/profile";
import { SITE_NAME, SITE_URL } from "@/lib/site";

export default async function SiteLayout({ children }: { children: ReactNode }) {
  const profile = await getProfile();

  return (
    <>
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "WebSite",
          url: SITE_URL,
          name: profile?.name ?? SITE_NAME,
        }}
      />
      {profile ? (
        <JsonLd
          data={{
            "@context": "https://schema.org",
            "@type": "Person",
            name: profile.name,
            url: SITE_URL,
            jobTitle: profile.headline,
            ...(profile.email ? { email: profile.email } : {}),
            ...(profile.socials?.length
              ? { sameAs: profile.socials.map((s) => s.url) }
              : {}),
          }}
        />
      ) : null}

      <div id="top" />
      <Nav />
      <main id="main-content" className="flex-1">
        {children}
      </main>
      <Footer />
    </>
  );
}
