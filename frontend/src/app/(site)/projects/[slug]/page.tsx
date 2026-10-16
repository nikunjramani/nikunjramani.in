import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ArrowRight } from "lucide-react";

import { JsonLd } from "@/site/components/json-ld";
import { ProjectDetailView } from "@/site/components/project/project-detail-view";
import { Container } from "@/site/components/spec";
import { getProfile } from "@/lib/data/profile";
import { getAllProjects, getProjectBySlug } from "@/lib/data/projects";
import { SITE_NAME, SITE_URL } from "@/lib/site";

// No generateStaticParams: pages render per request (ADR 0014), so pre-building them would
// only add a Firestore dependency to `next build`.

type Params = Promise<{ slug: string }>;

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { slug } = await params;
  const project = await getProjectBySlug(slug);
  if (!project) return {};

  // Next only falls back to the file-convention opengraph-image.tsx in this route when
  // `openGraph` has no `images` key at all — even `images: undefined` still counts as the
  // key being present (see mergeStaticMetadata's `hasOwnProperty` check) and suppresses it.
  // So the key is only added at all when there's an explicit override to put in it.
  const explicitImage = project.seo?.ogImageUrl ?? project.cover?.url;

  return {
    title: project.seo?.metaTitle ?? project.title,
    description: project.seo?.metaDescription ?? project.summary,
    keywords: project.seo?.keywords,
    alternates: { canonical: `/projects/${slug}` },
    // Unlisted: reachable by link, kept out of search results.
    ...(project.visibility === "unlisted" ? { robots: { index: false, follow: true } } : {}),
    openGraph: {
      title: project.seo?.metaTitle ?? project.title,
      description: project.seo?.metaDescription ?? project.summary,
      url: `${SITE_URL}/projects/${slug}`,
      type: "article",
      ...(explicitImage ? { images: [explicitImage] } : {}),
    },
  };
}

export default async function ProjectDetailPage({ params }: { params: Params }) {
  const { slug } = await params;
  const [project, allProjects, profile] = await Promise.all([
    getProjectBySlug(slug),
    getAllProjects(),
    getProfile(),
  ]);

  if (!project) notFound();

  const index = allProjects.findIndex((p) => p.slug === slug);
  const prev = index > 0 ? allProjects[index - 1] : null;
  const next = index >= 0 && index < allProjects.length - 1 ? allProjects[index + 1] : null;

  return (
    <Container>
      <article className="pt-10 sm:pt-14">
        <JsonLd
          data={{
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            itemListElement: [
              { "@type": "ListItem", position: 1, name: "Home", item: SITE_URL },
              { "@type": "ListItem", position: 2, name: "Projects", item: `${SITE_URL}/projects` },
              { "@type": "ListItem", position: 3, name: project.title, item: `${SITE_URL}/projects/${slug}` },
            ],
          }}
        />
        <JsonLd
          data={{
            "@context": "https://schema.org",
            "@type": "CreativeWork",
            name: project.title,
            description: project.summary,
            url: `${SITE_URL}/projects/${slug}`,
            ...(project.cover ? { image: project.cover.url } : {}),
            ...(project.tags?.length ? { keywords: project.tags.join(", ") } : {}),
            author: { "@type": "Person", name: profile?.name ?? SITE_NAME },
          }}
        />

        <Link
          href="/projects"
          className="mb-10 inline-flex items-center gap-2 font-mono text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" /> All projects
        </Link>

        <ProjectDetailView project={project} />

        {prev || next ? (
          <nav aria-label="More projects" className="mt-12 grid gap-px border-y border-border sm:grid-cols-2">
            {prev ? (
              <Link href={`/projects/${prev.slug}`} className="group flex flex-col gap-1 py-6 sm:pr-6">
                <span className="inline-flex items-center gap-2 font-mono text-xs text-muted-foreground">
                  <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" /> Previous
                </span>
                <span className="font-semibold font-stretch-112% underline decoration-transparent underline-offset-4 group-hover:decoration-accent">
                  {prev.title}
                </span>
              </Link>
            ) : (
              <span />
            )}
            {next ? (
              <Link
                href={`/projects/${next.slug}`}
                className="group flex flex-col gap-1 py-6 sm:items-end sm:pl-6 sm:text-right"
              >
                <span className="inline-flex items-center gap-2 font-mono text-xs text-muted-foreground">
                  Next <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                </span>
                <span className="font-semibold font-stretch-112% underline decoration-transparent underline-offset-4 group-hover:decoration-accent">
                  {next.title}
                </span>
              </Link>
            ) : null}
          </nav>
        ) : null}
      </article>
    </Container>
  );
}
