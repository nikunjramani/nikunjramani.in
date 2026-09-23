import Image from "next/image";
import { Quote } from "lucide-react";

import { GalleryLightbox } from "@/components/site/project/gallery-lightbox";
import { OutcomeMetrics } from "@/components/site/project/outcome-metrics";
import { LinkIcon, linkTypeLabel } from "@/components/site/project/link-icon";
import { blurhashToDataURL } from "@/lib/blurhash";
import { cn } from "@/lib/utils";
import type { Project } from "@/generated/types";

const STATUS_LABEL: Record<string, string> = {
  concept: "Concept",
  "in-progress": "In progress",
  shipped: "Shipped",
  maintained: "Maintained",
  archived: "Archived",
};

/**
 * Every content block from the header through collaborators — the actual progressive-
 * disclosure rendering, shared between the public route and the admin editor's live
 * preview. Deliberately excludes JSON-LD, the "all projects" back link, and prev/next
 * navigation: those are page-level concerns (SEO metadata, sibling lookups) that don't
 * apply to a draft being previewed before it has ever been saved. Splitting this out is
 * what makes "preview must use the real components" (5.7) actually true rather than
 * aspirational — a second, hand-maintained preview renderer would drift from this one the
 * first time either changed without the other.
 */
export function ProjectDetailView({ project }: { project: Project }) {
  const content = project.content;
  const primaryLink = project.links?.find((l) => l.primary) ?? project.links?.[0];
  const secondaryLinks = project.links?.filter((l) => l !== primaryLink) ?? [];

  const stackByCategory = new Map<string, typeof project.stack>();
  for (const tech of project.stack ?? []) {
    const category = tech.category ?? "other";
    stackByCategory.set(category, [...(stackByCategory.get(category) ?? []), tech]);
  }

  const clientLabel = project.client?.confidential
    ? (project.client.publicLabel ?? "a confidential client")
    : project.client?.name;

  return (
    <>
      {/* Header */}
      <header className="mb-10 flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <span className="rounded-full border border-border px-2.5 py-0.5 text-xs text-muted-foreground">
            {STATUS_LABEL[project.status] ?? project.status}
          </span>
          {project.timeline?.displayLabel ? (
            <span className="text-xs text-muted-foreground">{project.timeline.displayLabel}</span>
          ) : null}
          {clientLabel ? <span className="text-xs text-muted-foreground">for {clientLabel}</span> : null}
        </div>

        <h1 className="text-3xl font-semibold tracking-tight text-balance">{project.title || "Untitled project"}</h1>
        {project.subtitle ? (
          <p className="text-lg text-muted-foreground text-balance">{project.subtitle}</p>
        ) : null}

        {project.links?.length ? (
          <div className="flex flex-wrap gap-3 pt-2">
            {primaryLink ? (
              <a
                href={primaryLink.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-md bg-accent px-4 py-2 text-sm text-accent-foreground transition-opacity hover:opacity-90"
              >
                <LinkIcon type={primaryLink.type} className="h-4 w-4" />
                {primaryLink.label ?? linkTypeLabel(primaryLink.type)}
              </a>
            ) : null}
            {secondaryLinks.map((link) => (
              <a
                key={link.url}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-md border border-border px-4 py-2 text-sm transition-colors hover:bg-muted"
              >
                <LinkIcon type={link.type} className="h-4 w-4" />
                {link.label ?? linkTypeLabel(link.type)}
              </a>
            ))}
          </div>
        ) : null}
      </header>

      {/* Cover */}
      {project.cover ? (
        <div className="relative mb-12 aspect-video w-full overflow-hidden rounded-lg bg-muted">
          <Image
            src={project.cover.url}
            alt={project.cover.alt}
            fill
            priority
            sizes="(min-width: 768px) 896px, 100vw"
            className="object-cover"
            placeholder={project.cover.blurhash ? "blur" : "empty"}
            blurDataURL={project.cover.blurhash ? blurhashToDataURL(project.cover.blurhash) : undefined}
          />
        </div>
      ) : null}

      <div className="flex flex-col gap-12">
        {/* Overview / problem / approach */}
        {content?.overview || content?.problem || content?.approach ? (
          <section className="flex flex-col gap-8">
            {content?.overview ? (
              <div>
                <h2 className="mb-2 text-sm font-medium text-muted-foreground uppercase tracking-wide">
                  Overview
                </h2>
                <p className="whitespace-pre-wrap text-foreground">{content.overview}</p>
              </div>
            ) : null}
            {content?.problem ? (
              <div>
                <h2 className="mb-2 text-sm font-medium text-muted-foreground uppercase tracking-wide">
                  Problem
                </h2>
                <p className="whitespace-pre-wrap text-foreground">{content.problem}</p>
              </div>
            ) : null}
            {content?.approach ? (
              <div>
                <h2 className="mb-2 text-sm font-medium text-muted-foreground uppercase tracking-wide">
                  Approach
                </h2>
                <p className="whitespace-pre-wrap text-foreground">{content.approach}</p>
              </div>
            ) : null}
          </section>
        ) : null}

        {/* Architecture */}
        {content?.architecture?.description ||
        content?.architecture?.diagram ||
        content?.architecture?.components?.length ? (
          <section>
            <h2 className="mb-4 text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Architecture
            </h2>
            {content.architecture?.description ? (
              <p className="mb-6 whitespace-pre-wrap text-foreground">{content.architecture.description}</p>
            ) : null}
            {content.architecture?.diagram ? (
              <div className="relative mb-6 aspect-video w-full overflow-hidden rounded-lg border border-border bg-surface">
                <Image
                  src={content.architecture.diagram.url}
                  alt={content.architecture.diagram.alt}
                  fill
                  sizes="(min-width: 768px) 896px, 100vw"
                  className="object-contain"
                />
              </div>
            ) : null}
            {content.architecture?.components?.length ? (
              <ul className="grid gap-3 sm:grid-cols-2">
                {content.architecture.components.map((component) => (
                  <li key={component.name} className="rounded-lg border border-border bg-surface p-4">
                    <p className="font-medium">{component.name}</p>
                    {component.role ? <p className="mt-1 text-sm text-muted-foreground">{component.role}</p> : null}
                    {component.tech ? <p className="mt-1 text-xs text-muted-foreground">{component.tech}</p> : null}
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        ) : null}

        {/* Challenges */}
        {content?.challenges?.length ? (
          <section>
            <h2 className="mb-4 text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Challenges
            </h2>
            <ul className="flex flex-col gap-4">
              {content.challenges.map((challenge) => (
                <li key={challenge.title} className="border-l-2 border-border pl-4">
                  <p className="font-medium">{challenge.title}</p>
                  {challenge.detail ? (
                    <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground">{challenge.detail}</p>
                  ) : null}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {/* Outcomes — the part a recruiter actually reads */}
        {content?.outcomes?.length ? (
          <section>
            <h2 className="mb-4 text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Outcomes
            </h2>
            <OutcomeMetrics metrics={content.outcomes} />
          </section>
        ) : null}

        {/* Learnings / future work */}
        {content?.learnings?.length || content?.futureWork?.length ? (
          <section className="grid gap-8 sm:grid-cols-2">
            {content?.learnings?.length ? (
              <div>
                <h2 className="mb-3 text-sm font-medium text-muted-foreground uppercase tracking-wide">
                  Learnings
                </h2>
                <ul className="flex flex-col gap-2">
                  {content.learnings.map((item) => (
                    <li key={item} className="text-sm text-foreground">
                      · {item}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {content?.futureWork?.length ? (
              <div>
                <h2 className="mb-3 text-sm font-medium text-muted-foreground uppercase tracking-wide">
                  Future work
                </h2>
                <ul className="flex flex-col gap-2">
                  {content.futureWork.map((item) => (
                    <li key={item} className="text-sm text-foreground">
                      · {item}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>
        ) : null}

        {/* Stack, grouped by category */}
        {project.stack?.length ? (
          <section>
            <h2 className="mb-4 text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Stack
            </h2>
            <div className="flex flex-col gap-4">
              {[...stackByCategory.entries()].map(([category, techs]) => (
                <div key={category} className="flex flex-wrap items-center gap-2">
                  <span className="w-24 shrink-0 text-xs text-muted-foreground capitalize">{category}</span>
                  <div className="flex flex-wrap gap-1.5">
                    {techs?.map((tech) => (
                      <span
                        key={tech.name}
                        className={cn(
                          "rounded-full px-2.5 py-1 text-xs",
                          tech.primary ? "bg-accent/10 text-accent" : "bg-muted text-muted-foreground",
                        )}
                      >
                        {tech.name}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {/* Gallery */}
        {project.gallery?.length ? (
          <section>
            <h2 className="mb-4 text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Gallery
            </h2>
            <GalleryLightbox items={project.gallery} />
          </section>
        ) : null}

        {/* Testimonial */}
        {project.testimonial ? (
          <section className="rounded-lg border border-border bg-surface p-6">
            <Quote className="mb-3 h-5 w-5 text-accent" aria-hidden="true" />
            <p className="text-lg text-balance">&ldquo;{project.testimonial.quote}&rdquo;</p>
            <p className="mt-3 text-sm text-muted-foreground">
              {project.testimonial.author}
              {project.testimonial.role ? `, ${project.testimonial.role}` : ""}
            </p>
          </section>
        ) : null}

        {/* Awards */}
        {project.awards?.length ? (
          <section>
            <h2 className="mb-4 text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Awards
            </h2>
            <ul className="flex flex-col gap-2">
              {project.awards.map((award) => (
                <li key={award.title} className="text-sm text-foreground">
                  {award.title}
                  {award.issuer ? ` — ${award.issuer}` : ""}
                  {award.year ? ` (${award.year})` : ""}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {/* Collaborators */}
        {project.collaborators?.length ? (
          <section>
            <h2 className="mb-4 text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Collaborators
            </h2>
            <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
              {project.collaborators.map((person) => (
                <li key={person.name}>
                  {person.name}
                  {person.role ? ` · ${person.role}` : ""}
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    </>
  );
}
