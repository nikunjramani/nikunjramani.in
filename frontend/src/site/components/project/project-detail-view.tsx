import Image from "next/image";

import { GalleryLightbox } from "@/site/components/project/gallery-lightbox";
import { OutcomeMetrics } from "@/site/components/project/outcome-metrics";
import { LinkIcon, linkTypeLabel } from "@/site/components/project/link-icon";
import { SpecSection, SpecTable } from "@/site/components/spec";
import { buttonPrimary, buttonSecondary, chip, chipPrimary } from "@/site/components/styles";
import { blurhashToDataURL } from "@/lib/blurhash";
import type { Project } from "@/generated/types";

const STATUS_LABEL: Record<string, string> = {
  concept: "Concept",
  "in-progress": "In progress",
  shipped: "Shipped",
  maintained: "Maintained",
  archived: "Archived",
};

const KIND_LABEL: Record<string, string> = {
  professional: "Professional",
  personal: "Personal",
  "open-source": "Open source",
  academic: "Academic",
  freelance: "Freelance",
  experiment: "Experiment",
};

/** Square markers, signal-coloured — the site's bullet (.docs/DESIGN.md). */
const bulletList = "flex list-[square] flex-col gap-2 pl-5 marker:text-accent";

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
    ? (project.client.publicLabel ?? "A confidential client")
    : project.client?.name;

  const team = [
    project.team?.size ? `${project.team.size} people` : null,
    project.team?.myScope,
  ]
    .filter(Boolean)
    .join(". ");

  return (
    <>
      {/* Header: what it is on the left, the facts in a title block on the right. */}
      <header className="grid gap-10 pb-12 lg:grid-cols-[1fr_20rem] lg:items-end lg:gap-16">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight font-stretch-125% text-balance sm:text-[2.75rem] sm:leading-[1.05]">
            {project.title || "Untitled project"}
          </h1>
          {project.subtitle ? (
            <p className="mt-4 max-w-2xl text-lg text-muted-foreground text-pretty">{project.subtitle}</p>
          ) : null}

          {project.links?.length ? (
            <div className="mt-8 flex flex-wrap gap-3">
              {primaryLink ? (
                <a href={primaryLink.url} target="_blank" rel="noopener noreferrer" className={buttonPrimary}>
                  <LinkIcon type={primaryLink.type} className="h-4 w-4" />
                  {primaryLink.label ?? linkTypeLabel(primaryLink.type)}
                </a>
              ) : null}
              {secondaryLinks.map((link) => (
                <a key={link.url} href={link.url} target="_blank" rel="noopener noreferrer" className={buttonSecondary}>
                  <LinkIcon type={link.type} className="h-4 w-4" />
                  {link.label ?? linkTypeLabel(link.type)}
                </a>
              ))}
            </div>
          ) : null}
        </div>

        <SpecTable
          rows={[
            { key: "Status", value: STATUS_LABEL[project.status] ?? project.status },
            project.timeline?.displayLabel && { key: "Timeline", value: project.timeline.displayLabel },
            { key: "Kind", value: KIND_LABEL[project.kind] ?? project.kind },
            project.role && { key: "Role", value: project.role },
            team && { key: "Team", value: team },
            clientLabel && { key: "Client", value: clientLabel },
          ]}
        />
      </header>

      {project.cover ? (
        <div className="relative mb-4 aspect-video w-full overflow-hidden rounded-(--radius) border border-border bg-muted">
          <Image
            src={project.cover.url}
            alt={project.cover.alt}
            fill
            priority
            sizes="(min-width: 1152px) 1104px, 100vw"
            className="object-cover"
            placeholder={project.cover.blurhash ? "blur" : "empty"}
            blurDataURL={project.cover.blurhash ? blurhashToDataURL(project.cover.blurhash) : undefined}
          />
        </div>
      ) : null}

      {content?.overview ? (
        <SpecSection title="Overview">
          <p className="max-w-[68ch] whitespace-pre-wrap text-lg text-pretty">{content.overview}</p>
        </SpecSection>
      ) : null}

      {content?.problem ? (
        <SpecSection title="Problem">
          <p className="max-w-[68ch] whitespace-pre-wrap text-pretty">{content.problem}</p>
        </SpecSection>
      ) : null}

      {content?.approach ? (
        <SpecSection title="Approach">
          <p className="max-w-[68ch] whitespace-pre-wrap text-pretty">{content.approach}</p>
        </SpecSection>
      ) : null}

      {/* Outcomes — the part a recruiter actually reads, so it comes before the detail. */}
      {content?.outcomes?.length ? (
        <SpecSection title="Outcomes">
          <OutcomeMetrics metrics={content.outcomes} />
        </SpecSection>
      ) : null}

      {content?.architecture?.description ||
      content?.architecture?.diagram ||
      content?.architecture?.components?.length ? (
        <SpecSection title="Architecture">
          {content.architecture?.description ? (
            <p className="mb-8 max-w-[68ch] whitespace-pre-wrap text-pretty">{content.architecture.description}</p>
          ) : null}
          {content.architecture?.diagram ? (
            <div className="relative mb-8 aspect-video w-full overflow-hidden rounded-(--radius) border border-border bg-surface">
              <Image
                src={content.architecture.diagram.url}
                alt={content.architecture.diagram.alt}
                fill
                sizes="(min-width: 1152px) 880px, 100vw"
                className="object-contain"
              />
            </div>
          ) : null}
          {content.architecture?.components?.length ? (
            <dl className="border-t border-border">
              {content.architecture.components.map((component) => (
                <div
                  key={component.name}
                  className="grid gap-1 border-b border-border py-3 sm:grid-cols-[12rem_1fr] sm:gap-6"
                >
                  <dt className="font-medium">{component.name}</dt>
                  <dd className="text-sm text-muted-foreground">
                    {component.role}
                    {component.tech ? (
                      <span className="mt-1 block font-mono text-xs">{component.tech}</span>
                    ) : null}
                  </dd>
                </div>
              ))}
            </dl>
          ) : null}
        </SpecSection>
      ) : null}

      {content?.challenges?.length ? (
        <SpecSection title="Challenges">
          <ul className="flex flex-col gap-6">
            {content.challenges.map((challenge) => (
              <li key={challenge.title} className="max-w-[68ch] border-l-2 border-accent pl-4">
                <p className="font-medium">{challenge.title}</p>
                {challenge.detail ? (
                  <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground text-pretty">
                    {challenge.detail}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </SpecSection>
      ) : null}

      {content?.learnings?.length ? (
        <SpecSection title="Learnings">
          <ul className={`${bulletList} max-w-[68ch]`}>
            {content.learnings.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </SpecSection>
      ) : null}

      {content?.futureWork?.length ? (
        <SpecSection title="Next">
          <ul className={`${bulletList} max-w-[68ch]`}>
            {content.futureWork.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </SpecSection>
      ) : null}

      {project.stack?.length ? (
        <SpecSection title="Stack">
          <dl className="border-t border-border">
            {[...stackByCategory.entries()].map(([category, techs]) => (
              <div key={category} className="grid gap-2 border-b border-border py-3 sm:grid-cols-[7.5rem_1fr] sm:gap-4">
                <dt className="pt-0.5 font-mono text-xs text-muted-foreground capitalize">{category}</dt>
                <dd>
                  <ul className="flex flex-wrap gap-1.5">
                    {techs?.map((tech) => (
                      <li key={tech.name} className={tech.primary ? chipPrimary : chip}>
                        {tech.name}
                      </li>
                    ))}
                  </ul>
                </dd>
              </div>
            ))}
          </dl>
        </SpecSection>
      ) : null}

      {project.gallery?.length ? (
        <SpecSection title="Gallery">
          <GalleryLightbox items={project.gallery} />
        </SpecSection>
      ) : null}

      {project.testimonial ? (
        <SpecSection title="Testimonial">
          <figure className="max-w-[68ch] border-l-2 border-accent pl-6">
            <blockquote className="text-xl text-pretty">&ldquo;{project.testimonial.quote}&rdquo;</blockquote>
            <figcaption className="mt-4 text-sm text-muted-foreground">
              {project.testimonial.author}
              {project.testimonial.role ? `, ${project.testimonial.role}` : ""}
            </figcaption>
          </figure>
        </SpecSection>
      ) : null}

      {project.awards?.length ? (
        <SpecSection title="Awards">
          <ul className={bulletList}>
            {project.awards.map((award) => (
              <li key={award.title}>
                {award.title}
                {award.issuer ? <span className="text-muted-foreground">, {award.issuer}</span> : null}
                {award.year ? <span className="ml-2 font-mono text-xs text-muted-foreground">{award.year}</span> : null}
              </li>
            ))}
          </ul>
        </SpecSection>
      ) : null}

      {project.collaborators?.length ? (
        <SpecSection title="With">
          <ul className="flex flex-col gap-1">
            {project.collaborators.map((person) => (
              <li key={person.name}>
                {person.name}
                {person.role ? <span className="text-muted-foreground">, {person.role}</span> : null}
              </li>
            ))}
          </ul>
        </SpecSection>
      ) : null}
    </>
  );
}
