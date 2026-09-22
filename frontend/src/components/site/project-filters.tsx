"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import { cn } from "@/lib/utils";

type FilterKey = "kind" | "status" | "tech";

function FilterGroup({
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
    <div>
      <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">{label}</p>
      <div className="flex flex-wrap gap-1.5">
        <Link
          href={hrefFor(null)}
          className={cn(
            "rounded-full border px-3 py-1 text-sm transition-colors",
            !active ? "border-accent text-accent" : "border-border text-muted-foreground hover:text-foreground",
          )}
        >
          All
        </Link>
        {options.map((option) => (
          <Link
            key={option}
            href={hrefFor(option)}
            aria-current={active === option ? "true" : undefined}
            className={cn(
              "rounded-full border px-3 py-1 text-sm capitalize transition-colors",
              active === option
                ? "border-accent text-accent"
                : "border-border text-muted-foreground hover:text-foreground",
            )}
          >
            {option}
          </Link>
        ))}
      </div>
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
    <div className="flex flex-col gap-4 border-y border-border py-6">
      <FilterGroup label="Kind" filterKey="kind" options={kinds} active={active.kind} />
      <FilterGroup label="Status" filterKey="status" options={statuses} active={active.status} />
      <FilterGroup label="Tech" filterKey="tech" options={techs} active={active.tech} />
    </div>
  );
}
