"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/projects", label: "Projects" },
  { href: "/experience", label: "Experience" },
  { href: "/about", label: "About" },
  { href: "/contact", label: "Contact" },
] as const;

/** A section is current on its own page and on everything under it (/projects/<slug>). */
function isCurrent(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function NavLinks() {
  const pathname = usePathname();
  return LINKS.map((link) => {
    const current = isCurrent(pathname, link.href);
    return (
      <Link
        key={link.href}
        href={link.href}
        aria-current={current ? "page" : undefined}
        className={cn(
          "relative px-3 py-2 font-mono text-xs transition-colors hover:text-foreground",
          current ? "text-foreground" : "text-muted-foreground",
        )}
      >
        {link.label}
        {current ? (
          <span aria-hidden="true" className="absolute inset-x-3 -bottom-[9px] h-0.5 bg-accent" />
        ) : null}
      </Link>
    );
  });
}

export function MobileMenu() {
  const pathname = usePathname();
  // The path the menu was opened on: navigating anywhere closes it, with no effect needed.
  const [openedAt, setOpenedAt] = useState<string | null>(null);
  const open = openedAt === pathname;

  return (
    <>
      <button
        type="button"
        aria-label={open ? "Close menu" : "Open menu"}
        aria-expanded={open}
        aria-controls="mobile-menu"
        onClick={() => setOpenedAt(open ? null : pathname)}
        className="inline-flex h-9 w-9 items-center justify-center rounded-(--radius) text-foreground"
      >
        {open ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
      </button>

      {open ? (
        <div
          id="mobile-menu"
          className="absolute inset-x-0 top-full border-b border-border bg-background px-4 py-2 sm:hidden"
        >
          <ul className="flex flex-col">
            {LINKS.map((link) => {
              const current = isCurrent(pathname, link.href);
              return (
                <li key={link.href} className="border-b border-border last:border-b-0">
                  <Link
                    href={link.href}
                    onClick={() => setOpenedAt(null)}
                    aria-current={current ? "page" : undefined}
                    className={cn(
                      "flex items-center gap-3 py-3 font-mono text-sm",
                      current ? "text-foreground" : "text-muted-foreground",
                    )}
                  >
                    <span
                      aria-hidden="true"
                      className={cn("h-2 w-2", current ? "bg-accent" : "bg-transparent")}
                    />
                    {link.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </>
  );
}
