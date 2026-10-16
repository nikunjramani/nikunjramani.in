import Image from "next/image";
import Link from "next/link";

import type { Project } from "@/generated/types";
import type { WithId } from "@/lib/data/convert";
import { blurhashToDataURL } from "@/lib/blurhash";

export function ProjectCard({ project }: { project: WithId<Project> }) {
  return (
    <Link
      href={`/projects/${project.slug}`}
      className="group flex flex-col overflow-hidden rounded-lg border border-border bg-surface transition-colors hover:border-accent"
    >
      {project.cover ? (
        <div className="relative aspect-video w-full overflow-hidden bg-muted">
          <Image
            src={project.cover.url}
            alt={project.cover.alt}
            fill
            sizes="(min-width: 640px) 50vw, 100vw"
            className="object-cover transition-transform group-hover:scale-[1.02]"
            placeholder={project.cover.blurhash ? "blur" : "empty"}
            blurDataURL={project.cover.blurhash ? blurhashToDataURL(project.cover.blurhash) : undefined}
          />
        </div>
      ) : (
        <div className="aspect-video w-full bg-muted" aria-hidden="true" />
      )}

      <div className="flex flex-1 flex-col gap-2 p-5">
        <div className="flex items-center justify-between gap-2">
          <h3 className="font-medium tracking-tight">{project.title}</h3>
          {project.timeline?.displayLabel ? (
            <span className="shrink-0 text-xs text-muted-foreground">
              {project.timeline.displayLabel}
            </span>
          ) : null}
        </div>
        <p className="line-clamp-2 text-sm text-muted-foreground">{project.summary}</p>

        {project.stack?.length ? (
          <div className="mt-auto flex flex-wrap gap-1.5 pt-3">
            {project.stack
              .filter((t) => t.primary)
              .slice(0, 4)
              .map((tech) => (
                <span
                  key={tech.name}
                  className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                >
                  {tech.name}
                </span>
              ))}
          </div>
        ) : null}
      </div>
    </Link>
  );
}
