import type { Metadata } from "next";
import Link from "next/link";

import { ProjectRow } from "@/site/components/project-row";
import { Container, SpecSection, SpecTable, textLink } from "@/site/components/spec";
import { buttonPrimary, buttonSecondary } from "@/site/components/styles";
import { getFeaturedProjects } from "@/lib/data/projects";
import { getProfile } from "@/lib/data/profile";
import { getFeaturedSkills } from "@/lib/data/skills";
import { SITE_NAME } from "@/lib/site";

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
    <>
      {/* Hero: the name, and a drawing title block of the facts a visitor scans for. */}
      <section className="relative overflow-hidden">
        <div aria-hidden="true" className="blueprint-grid pointer-events-none absolute inset-0" />
        <Container className="relative grid gap-12 pt-20 pb-16 sm:pt-28 sm:pb-20 lg:grid-cols-[1fr_22rem] lg:items-end lg:gap-16">
          <div>
            <h1 className="text-display leading-[0.95] font-semibold tracking-tight font-stretch-125% text-balance">
              {profile?.name ?? SITE_NAME}
            </h1>
            {profile?.headline ? (
              <p className="mt-6 max-w-2xl text-xl text-balance sm:text-2xl">{profile.headline}</p>
            ) : null}
            {profile?.tagline ? (
              <p className="mt-4 max-w-xl text-muted-foreground text-pretty">{profile.tagline}</p>
            ) : null}
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/projects" className={buttonPrimary}>
                View projects
              </Link>
              <Link href="/contact" className={buttonSecondary}>
                Get in touch
              </Link>
            </div>
          </div>

          <SpecTable
            animate
            className="lg:mb-1"
            rows={[
              profile?.availableForWork && {
                key: "Status",
                value: (
                  <span className="inline-flex items-center gap-2">
                    <span aria-hidden="true" className="h-2 w-2 bg-accent" />
                    Available for work
                  </span>
                ),
              },
              profile?.location && { key: "Based in", value: profile.location },
              skills.length > 0 && {
                key: "Works with",
                value: skills.map((s) => s.name).join(", "),
              },
              profile?.resumeUrl && {
                key: "Résumé",
                value: (
                  <a href={profile.resumeUrl} target="_blank" rel="noopener noreferrer" className="underline decoration-accent underline-offset-4">
                    Download PDF
                  </a>
                ),
              },
            ]}
          />
        </Container>
      </section>

      <Container>
        {projects.length ? (
          <SpecSection
            title="Selected work"
            action={
              <Link href="/projects" className={textLink}>
                All projects
              </Link>
            }
          >
            <ul className="border-t border-border">
              {projects.slice(0, 4).map((project) => (
                <ProjectRow key={project.id} project={project} />
              ))}
            </ul>
          </SpecSection>
        ) : null}

        <SpecSection title="Contact">
          <p className="max-w-xl text-lg text-pretty">
            {profile?.availableForWork
              ? "Have a project in mind? I'd love to hear about it."
              : "Send a message and I'll get back to you when I can."}
          </p>
          <Link href="/contact" className={`${buttonSecondary} mt-6`}>
            Send a message
          </Link>
        </SpecSection>
      </Container>
    </>
  );
}
