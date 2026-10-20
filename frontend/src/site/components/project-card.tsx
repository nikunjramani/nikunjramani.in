import Image from "next/image";
import Link from "next/link";

import { chipPrimary } from "@/site/components/styles";
import type { Project } from "@/generated/types";
import type { WithId } from "@/lib/data/api";
import { blurhashToDataURL } from "@/lib/blurhash";

/** A project on the index: a cover plate, then the title and its key facts. */
export function ProjectCard({ project }: { project: WithId<Project> }) {
  const primaryStack = project.stack?.filter((t) => t.primary).slice(0, 4) ?? [];
  const headline = project.metrics?.find((m) => m.highlight) ?? project.metrics?.[0];
  const figure = headline?.after ?? headline?.value;

  return (
    <Link
      href={`/projects/${project.slug}`}
      className="group flex flex-col border-t border-border pt-4"
    >
      {project.cover ? (
        <div className="relative mb-5 aspect-[16/10] w-full overflow-hidden rounded-(--radius) border border-border bg-muted">
          <Image
            src={project.cover.url}
            alt={project.cover.alt}
            fill
            sizes="(min-width: 1024px) 560px, (min-width: 640px) 50vw, 100vw"
            className="object-cover"
            placeholder={project.cover.blurhash ? "blur" : "empty"}
            blurDataURL={project.cover.blurhash ? blurhashToDataURL(project.cover.blurhash) : undefined}
          />
        </div>
      ) : null}

      <div className="flex items-baseline justify-between gap-4">
        <h2 className="text-lg font-semibold tracking-tight font-stretch-112% text-balance underline decoration-transparent underline-offset-4 transition-colors group-hover:decoration-accent">
          {project.title}
        </h2>
        {project.timeline?.displayLabel ? (
          <span className="shrink-0 font-mono text-xs text-muted-foreground">{project.timeline.displayLabel}</span>
        ) : null}
      </div>
      <p className="mt-2 text-sm text-muted-foreground text-pretty">{project.summary}</p>

      {headline && figure ? (
        <p className="mt-3 text-sm">
          <span className="font-mono font-medium text-accent">{figure}</span>{" "}
          <span className="text-muted-foreground">{headline.label}</span>
        </p>
      ) : null}

      {primaryStack.length ? (
        <ul className="mt-4 flex flex-wrap gap-1.5" aria-label="Main technologies">
          {primaryStack.map((tech) => (
            <li key={tech.name} className={chipPrimary}>
              {tech.name}
            </li>
          ))}
        </ul>
      ) : null}
    </Link>
  );
}
