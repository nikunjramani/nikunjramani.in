// Content changes must reach visitors without a stale CDN response (ADR 0014).
export const revalidate = 0;

import type { Metadata } from "next";
import type { ReactNode } from "react";

import { getProfile } from "@/lib/data/profile";
import { SITE_NAME, SITE_URL } from "@/lib/site";
import { SkipLink } from "@/shared/components/skip-link";
import { ThemeProvider } from "@/shared/components/theme-provider";
import { fontVariables } from "@/shared/fonts";
import { Footer } from "@/site/components/footer";
import { JsonLd } from "@/site/components/json-ld";
import { Nav } from "@/site/components/nav";

import "@/site/site.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: SITE_NAME, template: `%s — ${SITE_NAME}` },
  description: "Portfolio and writing.",
};

/** Root layout of the public site — one of two; the admin has its own (ADR 0021). */
export default async function SiteLayout({ children }: { children: ReactNode }) {
  const profile = await getProfile();

  return (
    <html lang="en" suppressHydrationWarning className={`${fontVariables} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">
        <SkipLink />
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
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
        </ThemeProvider>
      </body>
    </html>
  );
}
