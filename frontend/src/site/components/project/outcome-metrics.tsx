import type { Metric } from "@/generated/types";
import { cn } from "@/lib/utils";

/** Measured results as a ruled table of readings — the figure first, then what it measures. */
export function OutcomeMetrics({ metrics }: { metrics: Metric[] }) {
  return (
    <dl className="grid border-t border-l border-border sm:grid-cols-2 lg:grid-cols-3">
      {metrics.map((metric) => (
        <div
          key={metric.label}
          className={cn(
            "relative flex flex-col-reverse gap-2 border-r border-b border-border p-5",
            metric.highlight && "bg-accent/5",
          )}
        >
          {metric.highlight ? (
            <span aria-hidden="true" className="absolute inset-x-0 top-0 h-0.5 bg-accent" />
          ) : null}
          <dt className="text-sm text-muted-foreground text-pretty">{metric.label}</dt>
          <dd className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            {metric.before && metric.after ? (
              <>
                <span className="font-mono text-sm text-muted-foreground line-through">{metric.before}</span>
                <span className="text-2xl font-semibold tracking-tight font-stretch-112%">{metric.after}</span>
              </>
            ) : (
              <span className="text-2xl font-semibold tracking-tight font-stretch-112%">{metric.value}</span>
            )}
            {metric.delta ? <span className="font-mono text-sm text-accent">{metric.delta}</span> : null}
          </dd>
        </div>
      ))}
    </dl>
  );
}
