import type { Metadata } from "next";
import Image from "next/image";

import { Container, PageHeader } from "@/site/components/spec";
import { chip } from "@/site/components/styles";
import { getExperience } from "@/lib/data/experience";

export const metadata: Metadata = {
  title: "Experience",
  description: "Roles, achievements, and the tech behind each one.",
  alternates: { canonical: "/experience" },
};

function formatMonth(yyyyMm: string): string {
  const [year, month] = yyyyMm.split("-").map(Number);
  if (!year || !month) return yyyyMm;
  return new Date(year, month - 1).toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

export default async function ExperiencePage() {
  const roles = await getExperience();

  return (
    <Container>
      <PageHeader title="Experience" lede="Where I've worked, what I owned, and what changed because of it." />

      {roles.length ? (
        // A log, newest first: the dates are the left column, the role is the entry.
        <ol className="border-t border-border">
          {roles.map((role) => {
            const where = [role.location, role.remote ? "Remote" : null].filter(Boolean).join(", ");
            return (
              <li key={role.id} className="grid gap-4 border-b border-border py-10 lg:grid-cols-[11rem_1fr] lg:gap-12">
                <p className="font-mono text-xs text-muted-foreground lg:pt-1.5">
                  <time dateTime={role.startDate}>{formatMonth(role.startDate)}</time>
                  {" – "}
                  {role.current ? (
                    <span className="text-foreground">Present</span>
                  ) : role.endDate ? (
                    <time dateTime={role.endDate}>{formatMonth(role.endDate)}</time>
                  ) : null}
                </p>

                <div className="min-w-0">
                  <div className="flex items-start gap-4">
                    {role.companyLogo ? (
                      <div className="relative h-10 w-10 shrink-0 overflow-hidden rounded-(--radius) border border-border bg-muted">
                        <Image
                          src={role.companyLogo.url}
                          alt={role.companyLogo.alt}
                          fill
                          sizes="40px"
                          className="object-cover"
                        />
                      </div>
                    ) : null}
                    <div>
                      <h2 className="text-xl font-semibold tracking-tight font-stretch-112% text-balance">
                        {role.role}
                      </h2>
                      <p className="mt-1 text-muted-foreground">
                        {role.companyUrl ? (
                          <a
                            href={role.companyUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="underline decoration-border underline-offset-4 hover:text-foreground hover:decoration-accent"
                          >
                            {role.company}
                          </a>
                        ) : (
                          role.company
                        )}
                        {where ? <span className="text-sm">, {where}</span> : null}
                      </p>
                    </div>
                  </div>

                  {role.summary ? <p className="mt-5 max-w-[68ch] text-pretty">{role.summary}</p> : null}

                  {role.highlights?.length ? (
                    <ul className="mt-5 flex max-w-[68ch] list-[square] flex-col gap-2 pl-5 text-muted-foreground marker:text-accent">
                      {role.highlights.map((h) => (
                        <li key={h} className="text-pretty">
                          {h}
                        </li>
                      ))}
                    </ul>
                  ) : null}

                  {role.promotions?.length ? (
                    <ul className="mt-5 flex flex-col gap-1">
                      {role.promotions.map((p) => (
                        <li key={`${p.role}-${p.date}`} className="text-sm">
                          <span className="font-mono text-xs text-accent">{formatMonth(p.date)}</span>{" "}
                          Promoted to {p.role}
                        </li>
                      ))}
                    </ul>
                  ) : null}

                  {role.stack?.length ? (
                    <ul className="mt-6 flex flex-wrap gap-1.5" aria-label="Technologies">
                      {role.stack.map((tech) => (
                        <li key={tech.name} className={chip}>
                          {tech.name}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ol>
      ) : (
        <p className="text-muted-foreground">No roles are published yet.</p>
      )}
    </Container>
  );
}
