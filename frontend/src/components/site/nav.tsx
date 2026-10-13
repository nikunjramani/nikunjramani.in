import Link from "next/link";

import { MobileMenu, NavLinks } from "@/components/site/nav-links";
import { ThemeToggle } from "@/components/site/theme-toggle";
import { SITE_NAME } from "@/lib/site";

/** Server component — only the pieces that need the current path or open/closed state
 * (NavLinks, MobileMenu) and the theme toggle are client islands. CLAUDE.md rule 5. */
export function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <nav className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4" aria-label="Primary">
        <Link href="/" className="font-medium tracking-tight">
          {SITE_NAME}
        </Link>

        <div className="hidden items-center gap-1 sm:flex">
          <NavLinks />
          <ThemeToggle className="ml-2" />
        </div>

        <div className="flex items-center gap-2 sm:hidden">
          <ThemeToggle />
          <MobileMenu />
        </div>
      </nav>
    </header>
  );
}
