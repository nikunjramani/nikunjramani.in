"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Fragment } from "react";

import { ADMIN_SECTIONS } from "@/components/admin/admin-nav";

function labelFor(segment: string): string {
  const match = ADMIN_SECTIONS.find((s) => s.href.endsWith(`/${segment}`));
  if (match) return match.label;
  // A dynamic segment (a doc id) — not worth a network round trip just to show its title.
  return segment;
}

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean); // ["admin", "projects", "abc"]

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-sm text-muted-foreground">
      {segments.map((segment, i) => {
        const href = "/" + segments.slice(0, i + 1).join("/");
        const isLast = i === segments.length - 1;
        return (
          <Fragment key={href}>
            {i > 0 ? <span aria-hidden="true">/</span> : null}
            {isLast ? (
              <span className="text-foreground" aria-current="page">
                {labelFor(segment)}
              </span>
            ) : (
              <Link href={href} className="hover:text-foreground">
                {labelFor(segment)}
              </Link>
            )}
          </Fragment>
        );
      })}
    </nav>
  );
}
