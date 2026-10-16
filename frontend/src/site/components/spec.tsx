import type { CSSProperties, ReactNode } from "react";

import { cn } from "@/lib/utils";

/**
 * The site's two structural devices (.docs/DESIGN.md). A spec sheet, not a stack of cards:
 *
 * - <SpecTable> — key/value facts, ruled like a drawing's title block. Rows with no value are
 *   dropped, so optional fields never leave an empty key behind (ADR 0008).
 * - <SpecSection> — a page section as one spec row: the label in a left column on wide
 *   screens, stacked above the content on narrow ones.
 */

export type Spec = { key: string; value: ReactNode };

export function SpecTable({
  rows,
  animate = false,
  className,
}: {
  /** Falsy entries (a `cond && {…}` that didn't hold) are skipped. */
  rows: (Spec | null | false | "" | 0 | undefined)[];
  /** Draw the rules in on load — reserved for the one hero moment per page. */
  animate?: boolean;
  className?: string;
}) {
  const present = rows.filter((row): row is Spec => Boolean(row && row.value));
  if (!present.length) return null;

  return (
    <dl className={cn("relative text-sm", className)}>
      {present.map((row, i) => (
        <div key={row.key} className="relative grid grid-cols-[7.5rem_1fr] gap-4 py-2.5">
          <Rule animate={animate} row={i} />
          <dt className="font-mono text-xs leading-5 text-muted-foreground">{row.key}</dt>
          <dd className="min-w-0 leading-5">{row.value}</dd>
        </div>
      ))}
      <Rule animate={animate} row={present.length} bottom />
    </dl>
  );
}

function Rule({ animate, row, bottom = false }: { animate: boolean; row: number; bottom?: boolean }) {
  return (
    <span
      aria-hidden="true"
      style={animate ? ({ "--row": row } as CSSProperties) : undefined}
      className={cn(
        "absolute inset-x-0 h-px bg-border",
        bottom ? "bottom-0" : "top-0",
        animate && "draw-rule",
      )}
    />
  );
}

export function SpecSection({
  title,
  action,
  children,
  className,
}: {
  title: string;
  /** A link under the label, e.g. to the full list. */
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  const id = `section-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
  return (
    <section
      aria-labelledby={id}
      className={cn("grid gap-6 border-t border-border py-12 lg:grid-cols-[11rem_1fr] lg:gap-12", className)}
    >
      <div className="flex items-baseline justify-between gap-4 lg:flex-col lg:justify-start lg:gap-3">
        <h2 id={id} className="font-mono text-sm text-muted-foreground">
          {title}
        </h2>
        {action}
      </div>
      <div className="min-w-0">{children}</div>
    </section>
  );
}

/** The page column: wide enough for the spec layout, with a 16px gutter on phones. */
export function Container({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("mx-auto w-full max-w-6xl px-4 sm:px-6", className)}>{children}</div>;
}

/** The page-level heading every inner page opens with. */
export function PageHeader({ title, lede }: { title: string; lede?: ReactNode }) {
  return (
    <header className="pt-16 pb-10 sm:pt-20">
      <h1 className="text-3xl font-semibold tracking-tight font-stretch-112% text-balance">{title}</h1>
      {lede ? <p className="mt-3 max-w-2xl text-lg text-muted-foreground text-pretty">{lede}</p> : null}
    </header>
  );
}

/** Text link with the signal underline, for in-section actions. */
export const textLink =
  "font-mono text-xs text-muted-foreground underline decoration-border underline-offset-4 transition-colors hover:text-foreground hover:decoration-accent";
