import type { Metadata } from "next";

import { ProjectFilters } from "@/site/components/project-filters";
import { ProjectCard } from "@/site/components/project-card";
import { Container, PageHeader } from "@/site/components/spec";
import { getAllProjects } from "@/lib/data/projects";

export const metadata: Metadata = {
  title: "Projects",
  description: "A selection of things I've built.",
  // Filtered views (?kind=&tech=&status=) are near-duplicates of this page — canonicalizing
  // all of them here keeps search engines from indexing every filter combination separately.
  alternates: { canonical: "/projects" },
};

type SearchParams = Promise<{ kind?: string; tech?: string; status?: string }>;

export default async function ProjectsPage({ searchParams }: { searchParams: SearchParams }) {
  const [projects, params] = await Promise.all([getAllProjects(), searchParams]);

  const kinds = [...new Set(projects.map((p) => p.kind))].sort();
  const statuses = [...new Set(projects.map((p) => p.status))].sort();
  const techs = [...new Set(projects.flatMap((p) => p.stack?.map((t) => t.name) ?? []))].sort();

  const filtered = projects.filter((project) => {
    if (params.kind && project.kind !== params.kind) return false;
    if (params.status && project.status !== params.status) return false;
    if (params.tech && !project.stack?.some((t) => t.name === params.tech)) return false;
    return true;
  });
  const filteredBy = Boolean(params.kind || params.status || params.tech);

  return (
    <Container>
      <PageHeader title="Projects" lede="Things I've built, from first commit to production." />

      {projects.length > 1 ? (
        <ProjectFilters
          kinds={kinds}
          statuses={statuses}
          techs={techs}
          active={{ kind: params.kind, status: params.status, tech: params.tech }}
        />
      ) : null}

      <p className="mt-6 font-mono text-xs text-muted-foreground" aria-live="polite">
        {filteredBy
          ? `Showing ${filtered.length} of ${projects.length}`
          : `${projects.length} project${projects.length === 1 ? "" : "s"}`}
      </p>

      {filtered.length ? (
        <div className="mt-6 grid gap-x-10 gap-y-14 sm:grid-cols-2">
          {filtered.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      ) : (
        <p className="mt-12 text-muted-foreground">
          {projects.length
            ? "Nothing matches these filters. Clear one to see more."
            : "No projects are published yet."}
        </p>
      )}
    </Container>
  );
}
