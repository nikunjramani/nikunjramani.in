import Link from "next/link";

import { chipPrimary } from "@/site/components/styles";
import type { Project } from "@/generated/types";
import type { WithId } from "@/lib/data/convert";

/** One project as a ruled row — the home page's index of selected work. */
export function ProjectRow({ project }: { project: WithId<Project> }) {
  const primaryStack = project.stack?.filter((t) => t.primary).slice(0, 4) ?? [];

  return (
    <li className="border-b border-border">
      <Link
        href={`/projects/${project.slug}`}
        className="group grid gap-x-8 gap-y-3 py-6 sm:grid-cols-[1fr_8rem]"
      >
        <div className="min-w-0">
          <h3 className="text-lg font-semibold tracking-tight font-stretch-112% text-balance underline decoration-transparent underline-offset-4 transition-colors group-hover:decoration-accent">
            {project.title}
          </h3>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground text-pretty">{project.summary}</p>
          {primaryStack.length ? (
            <ul className="mt-3 flex flex-wrap gap-1.5" aria-label="Main technologies">
              {primaryStack.map((tech) => (
                <li key={tech.name} className={chipPrimary}>
                  {tech.name}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
        {project.timeline?.displayLabel ? (
          <p className="font-mono text-xs text-muted-foreground sm:pt-1.5 sm:text-right">
            {project.timeline.displayLabel}
          </p>
        ) : null}
      </Link>
    </li>
  );
}
