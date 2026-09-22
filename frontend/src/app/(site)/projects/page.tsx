import type { Metadata } from "next";

import { ProjectFilters } from "@/components/site/project-filters";
import { ProjectCard } from "@/components/site/project-card";
import { getAllProjects } from "@/lib/data/projects";

export const metadata: Metadata = {
  title: "Projects",
  description: "A selection of things I've built.",
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

  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <h1 className="mb-2 text-2xl font-semibold tracking-tight">Projects</h1>
      <p className="mb-8 text-muted-foreground">
        {projects.length} project{projects.length === 1 ? "" : "s"}, filterable by kind, tech and status.
      </p>

      <ProjectFilters
        kinds={kinds}
        statuses={statuses}
        techs={techs}
        active={{ kind: params.kind, status: params.status, tech: params.tech }}
      />

      {filtered.length ? (
        <div className="mt-8 grid gap-6 sm:grid-cols-2">
          {filtered.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      ) : (
        <p className="mt-16 text-center text-muted-foreground">
          {projects.length ? "No projects match these filters." : "No projects published yet."}
        </p>
      )}
    </div>
  );
}
