import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ArrowRight } from "lucide-react";

import { JsonLd } from "@/components/site/json-ld";
import { ProjectDetailView } from "@/components/site/project/project-detail-view";
import { getAllProjects, getProjectBySlug } from "@/lib/data/projects";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://nikunjramani.in";

type Params = Promise<{ slug: string }>;

export async function generateStaticParams() {
  const projects = await getAllProjects();
  return projects.map((project) => ({ slug: project.slug }));
}

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
  const [project, allProjects] = await Promise.all([getProjectBySlug(slug), getAllProjects()]);

  if (!project) notFound();

  const index = allProjects.findIndex((p) => p.slug === slug);
  const prev = index > 0 ? allProjects[index - 1] : null;
  const next = index >= 0 && index < allProjects.length - 1 ? allProjects[index + 1] : null;

  return (
    <article className="mx-auto max-w-4xl px-6 py-16">
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
          author: { "@type": "Person", name: "Nikunj Ramani" },
        }}
      />

      <Link
        href="/projects"
        className="mb-8 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" /> All projects
      </Link>

      <ProjectDetailView project={project} />

      {/* Prev / next */}
      {prev || next ? (
        <nav className="mt-16 flex items-center justify-between border-t border-border pt-8">
          {prev ? (
            <Link
              href={`/projects/${prev.slug}`}
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="h-4 w-4" /> {prev.title}
            </Link>
          ) : (
            <span />
          )}
          {next ? (
            <Link
              href={`/projects/${next.slug}`}
              className="flex items-center gap-1.5 text-right text-sm text-muted-foreground hover:text-foreground"
            >
              {next.title} <ArrowRight className="h-4 w-4" />
            </Link>
          ) : (
            <span />
          )}
        </nav>
      ) : null}
    </article>
  );
}
