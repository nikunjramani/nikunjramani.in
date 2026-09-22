import type { ReactNode } from "react";

import { Footer } from "@/components/site/footer";
import { Nav } from "@/components/site/nav";

export default function SiteLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <div id="top" />
      <Nav />
      <main id="main-content" className="flex-1">
        {children}
      </main>
      <Footer />
    </>
  );
}
