"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import { cn } from "@/lib/utils";

type FilterKey = "kind" | "status" | "tech";

const option =
  "rounded-(--radius) border px-2.5 py-1 font-mono text-xs transition-colors";
const optionOn = "border-accent bg-accent/10 text-foreground";
const optionOff = "border-border text-muted-foreground hover:border-foreground hover:text-foreground";

/** Filters are plain links (?kind=…), so every filtered view is a shareable, server-rendered URL. */
function FilterRow({
  label,
  filterKey,
  options,
  active,
}: {
  label: string;
  filterKey: FilterKey;
  options: string[];
  active?: string;
}) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  if (!options.length) return null;

  const hrefFor = (value: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value === null) {
      params.delete(filterKey);
    } else {
      params.set(filterKey, value);
    }
    const qs = params.toString();
    return qs ? `${pathname}?${qs}` : pathname;
  };

  return (
    <div className="grid gap-2 border-b border-border py-3 sm:grid-cols-[7.5rem_1fr] sm:gap-4">
      <p className="pt-1 font-mono text-xs text-muted-foreground" id={`filter-${filterKey}`}>
        {label}
      </p>
      <ul className="flex flex-wrap gap-1.5" aria-labelledby={`filter-${filterKey}`}>
        <li>
          <Link
            href={hrefFor(null)}
            aria-current={!active ? "true" : undefined}
            className={cn(option, !active ? optionOn : optionOff)}
          >
            All
          </Link>
        </li>
        {options.map((value) => (
          <li key={value}>
            <Link
              href={hrefFor(value)}
              aria-current={active === value ? "true" : undefined}
              className={cn(option, active === value ? optionOn : optionOff)}
            >
              {/* kind/status are slugs ("in-progress"); tech names are shown as written */}
              {filterKey === "tech" ? value : value.replace(/-/g, " ")}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ProjectFilters({
  kinds,
  statuses,
  techs,
  active,
}: {
  kinds: string[];
  statuses: string[];
  techs: string[];
  active: { kind?: string; status?: string; tech?: string };
}) {
  return (
    <div className="border-t border-border">
      <FilterRow label="Kind" filterKey="kind" options={kinds} active={active.kind} />
      <FilterRow label="Status" filterKey="status" options={statuses} active={active.status} />
      <FilterRow label="Tech" filterKey="tech" options={techs} active={active.tech} />
    </div>
  );
}
