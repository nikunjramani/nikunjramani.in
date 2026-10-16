import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SITE_NAME, SITE_URL } from "@/lib/site";
import { SkipLink } from "@/shared/components/skip-link";
import { ThemeProvider } from "@/shared/components/theme-provider";
import { fontVariables } from "@/admin/fonts";

import "@/admin/admin.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: `Admin — ${SITE_NAME}`, template: `%s — ${SITE_NAME}` },
  robots: { index: false, follow: false },
};

/** Root layout of the admin panel — separate document, stylesheet and design from the
 * public site (ADR 0021). Moving between /admin and the site is a full page load. */
export default function AdminRootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${fontVariables} h-full antialiased`}>
      <body className="min-h-full bg-background font-sans">
        <SkipLink />
        {/* Same storage key as the site, so the theme the owner picked there carries over. */}
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
