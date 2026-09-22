import type { Metadata } from "next";
import Image from "next/image";
import { Download } from "lucide-react";

import { Markdown } from "@/components/site/markdown";
import { SkillMatrix } from "@/components/site/skill-matrix";
import { blurhashToDataURL } from "@/lib/blurhash";
import { getProfile } from "@/lib/data/profile";
import { getSkills } from "@/lib/data/skills";
import { getEducations } from "@/lib/data/education";
import { getCertifications } from "@/lib/data/certifications";

export const metadata: Metadata = {
  title: "About",
  description: "Background, skills, and how I got here.",
  alternates: { canonical: "/about" },
};

export default async function AboutPage() {
  const [profile, skills, educations, certifications] = await Promise.all([
    getProfile(),
    getSkills(),
    getEducations(),
    getCertifications(),
  ]);

  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <header className="mb-12 flex flex-col items-start gap-6 sm:flex-row sm:items-center">
        {profile?.avatar ? (
          <div className="relative h-24 w-24 shrink-0 overflow-hidden rounded-full bg-muted">
            <Image
              src={profile.avatar.url}
              alt={profile.avatar.alt}
              fill
              sizes="96px"
              className="object-cover"
              placeholder={profile.avatar.blurhash ? "blur" : "empty"}
              blurDataURL={profile.avatar.blurhash ? blurhashToDataURL(profile.avatar.blurhash) : undefined}
            />
          </div>
        ) : null}
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{profile?.name ?? "About"}</h1>
          {profile?.headline ? <p className="mt-1 text-lg text-muted-foreground">{profile.headline}</p> : null}
          {profile?.location ? <p className="mt-1 text-sm text-muted-foreground">{profile.location}</p> : null}
        </div>
      </header>

      {profile?.bio ? (
        <section className="mb-14 max-w-2xl">
          <Markdown>{profile.bio}</Markdown>
        </section>
      ) : null}

      {profile?.resumeUrl ? (
        <section className="mb-14">
          <a
            href={profile.resumeUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-4 py-2 text-sm transition-colors hover:bg-muted"
          >
            <Download className="h-4 w-4" /> Download résumé
          </a>
        </section>
      ) : null}

      {skills.length ? (
        <section className="mb-14 border-t border-border pt-10">
          <h2 className="mb-6 text-sm font-medium text-muted-foreground uppercase tracking-wide">Skills</h2>
          <SkillMatrix skills={skills} />
        </section>
      ) : null}

      {educations.length ? (
        <section className="mb-14 border-t border-border pt-10">
          <h2 className="mb-6 text-sm font-medium text-muted-foreground uppercase tracking-wide">Education</h2>
          <ul className="flex flex-col gap-6">
            {educations.map((edu) => (
              <li key={edu.id}>
                <p className="font-medium">{edu.institution}</p>
                <p className="text-sm text-muted-foreground">
                  {edu.qualification}
                  {edu.field ? ` in ${edu.field}` : ""}
                </p>
                {edu.startYear ? (
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {edu.startYear}
                    {edu.endYear ? `–${edu.endYear}` : edu.endYear === null ? " – present" : ""}
                  </p>
                ) : null}
                {edu.highlights?.length ? (
                  <ul className="mt-2 flex flex-col gap-1">
                    {edu.highlights.map((h) => (
                      <li key={h} className="text-sm text-muted-foreground">
                        · {h}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {certifications.length ? (
        <section className="border-t border-border pt-10">
          <h2 className="mb-6 text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Certifications
          </h2>
          <ul className="grid gap-4 sm:grid-cols-2">
            {certifications.map((cert) => (
              <li key={cert.id} className="rounded-lg border border-border bg-surface p-4">
                {cert.credentialUrl ? (
                  <a
                    href={cert.credentialUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-medium hover:text-accent"
                  >
                    {cert.title}
                  </a>
                ) : (
                  <p className="font-medium">{cert.title}</p>
                )}
                <p className="mt-1 text-sm text-muted-foreground">{cert.issuer}</p>
                {cert.issuedOn ? (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Issued {new Date(cert.issuedOn).getFullYear()}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
