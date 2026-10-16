import Link from "next/link";

import { Container } from "@/site/components/spec";
import { MobileMenu, NavLinks } from "@/site/components/nav-links";
import { ThemeToggle } from "@/site/components/theme-toggle";
import { SITE_NAME } from "@/lib/site";

/** Server component — only the pieces that need the current path or open/closed state
 * (NavLinks, MobileMenu) and the theme toggle are client islands. CLAUDE.md rule 5. */
export function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/85 backdrop-blur">
      <Container className="relative">
        <nav className="flex h-14 items-center justify-between gap-6" aria-label="Primary">
          <Link href="/" className="text-sm font-semibold tracking-tight font-stretch-112%">
            {SITE_NAME}
          </Link>

          <div className="hidden items-center gap-1 sm:flex">
            <NavLinks />
            <ThemeToggle className="ml-3" />
          </div>

          <div className="flex items-center gap-2 sm:hidden">
            <ThemeToggle />
            <MobileMenu />
          </div>
        </nav>
      </Container>
    </header>
  );
}
