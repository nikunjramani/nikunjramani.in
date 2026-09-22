import type { Metadata } from "next";
import Image from "next/image";

import { getExperience } from "@/lib/data/experience";

export const metadata: Metadata = {
  title: "Experience",
  description: "Roles, achievements, and the tech behind each one.",
};

function formatMonth(yyyyMm: string): string {
  const [year, month] = yyyyMm.split("-").map(Number);
  if (!year || !month) return yyyyMm;
  return new Date(year, month - 1).toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

export default async function ExperiencePage() {
  const roles = await getExperience();

  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <h1 className="mb-10 text-2xl font-semibold tracking-tight">Experience</h1>

      {roles.length ? (
        <ol className="flex flex-col gap-10 border-l border-border pl-6">
          {roles.map((role) => (
            <li key={role.id} className="relative">
              <span className="absolute top-1.5 -left-[29px] h-2 w-2 rounded-full bg-accent" aria-hidden="true" />

              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="flex items-center gap-3">
                  {role.companyLogo ? (
                    <div className="relative h-9 w-9 shrink-0 overflow-hidden rounded-md bg-muted">
                      <Image src={role.companyLogo.url} alt={role.companyLogo.alt} fill sizes="36px" className="object-cover" />
                    </div>
                  ) : null}
                  <div>
                    <h2 className="font-medium tracking-tight">{role.role}</h2>
                    <p className="text-sm text-muted-foreground">
                      {role.companyUrl ? (
                        <a href={role.companyUrl} target="_blank" rel="noopener noreferrer" className="hover:text-foreground">
                          {role.company}
                        </a>
                      ) : (
                        role.company
                      )}
                      {role.location ? ` · ${role.location}` : ""}
                      {role.remote ? " · Remote" : ""}
                    </p>
                  </div>
                </div>
                <span className="shrink-0 text-xs text-muted-foreground">
                  {formatMonth(role.startDate)} – {role.current ? "Present" : role.endDate ? formatMonth(role.endDate) : ""}
                </span>
              </div>

              {role.summary ? <p className="mt-3 text-sm text-foreground">{role.summary}</p> : null}

              {role.highlights?.length ? (
                <ul className="mt-3 flex flex-col gap-1.5">
                  {role.highlights.map((h) => (
                    <li key={h} className="text-sm text-muted-foreground">
                      · {h}
                    </li>
                  ))}
                </ul>
              ) : null}

              {role.promotions?.length ? (
                <ul className="mt-3 flex flex-col gap-1">
                  {role.promotions.map((p) => (
                    <li key={`${p.role}-${p.date}`} className="text-xs text-accent">
                      Promoted to {p.role} · {formatMonth(p.date)}
                    </li>
                  ))}
                </ul>
              ) : null}

              {role.stack?.length ? (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {role.stack.map((tech) => (
                    <span key={tech.name} className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                      {tech.name}
                    </span>
                  ))}
                </div>
              ) : null}
            </li>
          ))}
        </ol>
      ) : (
        <p className="text-muted-foreground">Content for this page is still being written.</p>
      )}
    </div>
  );
}
