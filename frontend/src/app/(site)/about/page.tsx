import type { Metadata } from "next";
import Image from "next/image";
import { Download } from "lucide-react";

import { Markdown } from "@/site/components/markdown";
import { SkillMatrix } from "@/site/components/skill-matrix";
import { Container, SpecSection, SpecTable } from "@/site/components/spec";
import { buttonSecondary } from "@/site/components/styles";
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

function years(start?: number, end?: number | null) {
  if (!start) return null;
  if (end) return `${start}–${end}`;
  return end === null ? `${start}–present` : `${start}`;
}

export default async function AboutPage() {
  const [profile, skills, educations, certifications] = await Promise.all([
    getProfile(),
    getSkills(),
    getEducations(),
    getCertifications(),
  ]);

  return (
    <Container>
      <header className="grid gap-10 pt-16 pb-12 sm:pt-20 lg:grid-cols-[1fr_20rem] lg:items-end lg:gap-16">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end">
          {profile?.avatar ? (
            <div className="relative h-28 w-28 shrink-0 overflow-hidden rounded-(--radius) border border-border bg-muted">
              <Image
                src={profile.avatar.url}
                alt={profile.avatar.alt}
                fill
                sizes="112px"
                className="object-cover"
                placeholder={profile.avatar.blurhash ? "blur" : "empty"}
                blurDataURL={profile.avatar.blurhash ? blurhashToDataURL(profile.avatar.blurhash) : undefined}
              />
            </div>
          ) : null}
          <div>
            <h1 className="text-3xl font-semibold tracking-tight font-stretch-125% text-balance sm:text-[2.75rem] sm:leading-[1.05]">
              {profile?.name ?? "About"}
            </h1>
            {profile?.headline ? (
              <p className="mt-3 text-lg text-muted-foreground text-balance">{profile.headline}</p>
            ) : null}
          </div>
        </div>

        <SpecTable
          rows={[
            profile?.location && { key: "Based in", value: profile.location },
            profile?.availableForWork && { key: "Status", value: "Available for work" },
            skills.length > 0 && { key: "Skills", value: `${skills.length} across ${new Set(skills.map((s) => s.category)).size} areas` },
          ]}
        />
      </header>

      {profile?.bio || profile?.resumeUrl ? (
        <SpecSection title="Profile">
          {profile?.bio ? (
            <div className="max-w-[68ch] text-lg">
              <Markdown>{profile.bio}</Markdown>
            </div>
          ) : null}
          {profile?.resumeUrl ? (
            <a
              href={profile.resumeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={`${buttonSecondary} mt-8`}
            >
              <Download className="h-4 w-4" aria-hidden="true" /> Download résumé
            </a>
          ) : null}
        </SpecSection>
      ) : null}

      {skills.length ? (
        <SpecSection title="Skills">
          <SkillMatrix skills={skills} />
        </SpecSection>
      ) : null}

      {educations.length ? (
        <SpecSection title="Education">
          <ul className="border-t border-border">
            {educations.map((edu) => (
              <li key={edu.id} className="grid gap-2 border-b border-border py-5 sm:grid-cols-[1fr_8rem] sm:gap-8">
                <div>
                  <p className="font-semibold font-stretch-112%">{edu.institution}</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {edu.qualification}
                    {edu.field ? ` in ${edu.field}` : ""}
                  </p>
                  {edu.highlights?.length ? (
                    <ul className="mt-3 flex list-[square] flex-col gap-1 pl-5 text-sm marker:text-accent">
                      {edu.highlights.map((h) => (
                        <li key={h}>{h}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
                {years(edu.startYear, edu.endYear) ? (
                  <p className="font-mono text-xs text-muted-foreground sm:pt-1 sm:text-right">
                    {years(edu.startYear, edu.endYear)}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </SpecSection>
      ) : null}

      {certifications.length ? (
        <SpecSection title="Certifications">
          <ul className="border-t border-border">
            {certifications.map((cert) => (
              <li key={cert.id} className="grid gap-2 border-b border-border py-4 sm:grid-cols-[1fr_8rem] sm:gap-8">
                <div>
                  {cert.credentialUrl ? (
                    <a
                      href={cert.credentialUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium underline decoration-border underline-offset-4 hover:decoration-accent"
                    >
                      {cert.title}
                    </a>
                  ) : (
                    <p className="font-medium">{cert.title}</p>
                  )}
                  <p className="mt-1 text-sm text-muted-foreground">{cert.issuer}</p>
                </div>
                {cert.issuedOn ? (
                  <p className="font-mono text-xs text-muted-foreground sm:pt-1 sm:text-right">
                    {new Date(cert.issuedOn).getFullYear()}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </SpecSection>
      ) : null}
    </Container>
  );
}
