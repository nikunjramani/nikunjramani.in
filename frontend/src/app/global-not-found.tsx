import type { Metadata } from "next";

import { SITE_NAME } from "@/lib/site";
import { ThemeProvider } from "@/shared/components/theme-provider";
import { fontVariables } from "@/site/fonts";
import { NotFoundMessage } from "@/site/components/not-found-message";

import "@/site/site.css";

export const metadata: Metadata = {
  title: `Page not found — ${SITE_NAME}`,
};

/**
 * A URL that matches no route at all. With two root layouts there is no single layout to
 * render a 404 inside, so Next serves this complete document instead (ADR 0021). Styled as
 * the public site — that's where stray URLs come from — but without the nav and footer,
 * which would cost Firestore reads for a page nobody meant to visit.
 */
export default function GlobalNotFound() {
  return (
    <html lang="en" suppressHydrationWarning className={`${fontVariables} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <main id="main-content" className="flex-1">
            <NotFoundMessage />
          </main>
        </ThemeProvider>
      </body>
    </html>
  );
}
