import type { Metadata } from "next";
import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { ProjectCard } from "@/components/site/project-card";
import { SkillPills } from "@/components/site/skill-pills";
import { getFeaturedProjects } from "@/lib/data/projects";
import { getProfile } from "@/lib/data/profile";
import { getFeaturedSkills } from "@/lib/data/skills";

export const metadata: Metadata = {
  alternates: { canonical: "/" },
};

export default async function HomePage() {
  const [profile, skills, projects] = await Promise.all([
    getProfile(),
    getFeaturedSkills(),
    getFeaturedProjects(),
  ]);

  return (
    <div className="mx-auto max-w-4xl px-6">
      {/* Hero */}
      <section className="flex min-h-[70vh] flex-col justify-center gap-6 py-20">
        {profile?.availableForWork ? (
          <span className="inline-flex w-fit items-center gap-2 rounded-full border border-border px-3 py-1 text-xs text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            Available for work
          </span>
        ) : null}
        <h1 className="text-3xl font-semibold tracking-tight text-balance">
          {profile?.name ?? "Nikunj Ramani"}
        </h1>
        {profile?.headline ? (
          <p className="text-xl text-muted-foreground text-balance">{profile.headline}</p>
        ) : null}
        {profile?.tagline ? (
          <p className="max-w-xl text-muted-foreground">{profile.tagline}</p>
        ) : null}
        <div className="flex flex-wrap gap-3 pt-2">
          <Link
            href="/projects"
            className="inline-flex items-center gap-1.5 rounded-md bg-accent px-4 py-2 text-sm text-accent-foreground transition-opacity hover:opacity-90"
          >
            View projects <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            href="/contact"
            className="inline-flex items-center rounded-md border border-border px-4 py-2 text-sm transition-colors hover:bg-muted"
          >
            Get in touch
          </Link>
        </div>
      </section>

      {skills.length ? (
        <section className="border-t border-border py-16">
          <h2 className="mb-6 text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Skills
          </h2>
          <SkillPills skills={skills} />
        </section>
      ) : null}

      {projects.length ? (
        <section className="border-t border-border py-16">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Featured projects
            </h2>
            <Link href="/projects" className="text-sm text-muted-foreground hover:text-foreground">
              All projects →
            </Link>
          </div>
          <div className="grid gap-6 sm:grid-cols-2">
            {projects.slice(0, 4).map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        </section>
      ) : null}

      <section className="border-t border-border py-16">
        <h2 className="mb-3 text-xl font-medium tracking-tight">Let&apos;s work together</h2>
        <p className="mb-4 max-w-xl text-muted-foreground">
          {profile?.email
            ? "Have a project in mind? I'd love to hear about it."
            : "Content for this page is still being written."}
        </p>
        <Link
          href="/contact"
          className="inline-flex items-center gap-1.5 text-sm text-accent hover:underline"
        >
          Contact me <ArrowRight className="h-4 w-4" />
        </Link>
      </section>
    </div>
  );
}
