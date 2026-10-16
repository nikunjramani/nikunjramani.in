import type { Metric } from "@/generated/types";
import { cn } from "@/lib/utils";

export function OutcomeMetrics({ metrics }: { metrics: Metric[] }) {
  return (
    <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {metrics.map((metric) => (
        <div
          key={metric.label}
          className={cn(
            "rounded-lg border p-5",
            metric.highlight ? "border-accent bg-accent/5" : "border-border bg-surface",
          )}
        >
          <dt className="text-sm text-muted-foreground">{metric.label}</dt>
          <dd className="mt-1 flex items-baseline gap-2">
            {metric.before && metric.after ? (
              <>
                <span className="text-sm text-muted-foreground line-through">{metric.before}</span>
                <span className="text-xl font-semibold tracking-tight">{metric.after}</span>
              </>
            ) : (
              <span className="text-xl font-semibold tracking-tight">{metric.value}</span>
            )}
            {metric.delta ? (
              <span className="text-sm font-medium text-accent">{metric.delta}</span>
            ) : null}
          </dd>
        </div>
      ))}
    </dl>
  );
}
