import type { Skill } from "@/generated/types";
import type { WithId } from "@/lib/data/api";
import { cn } from "@/lib/utils";

const CATEGORY_LABEL: Record<string, string> = {
  backend: "Backend",
  frontend: "Frontend",
  "cloud-devops": "Cloud & DevOps",
  data: "Data",
  mobile: "Mobile",
  tools: "Tools",
};

/** Skills grouped by category, each read like a gauge: five segments, filled to the level. */
export function SkillMatrix({ skills }: { skills: WithId<Skill>[] }) {
  const byCategory = new Map<string, WithId<Skill>[]>();
  for (const skill of skills) {
    byCategory.set(skill.category, [...(byCategory.get(skill.category) ?? []), skill]);
  }

  return (
    <div className="grid gap-10 md:grid-cols-2 md:gap-x-12">
      {[...byCategory.entries()].map(([category, categorySkills]) => (
        <div key={category}>
          <h3 className="mb-2 font-semibold font-stretch-112%">{CATEGORY_LABEL[category] ?? category}</h3>
          <ul className="border-t border-border">
            {categorySkills.map((skill) => (
              <li
                key={skill.id}
                className="grid grid-cols-[1fr_auto_2.5rem] items-center gap-4 border-b border-border py-2.5"
                title={skill.blurb}
              >
                <span className="min-w-0 text-sm">{skill.name}</span>
                <span className="flex gap-0.5" role="img" aria-label={`Level ${skill.level} of 5`}>
                  {Array.from({ length: 5 }, (_, i) => (
                    <span
                      key={i}
                      className={cn("h-2.5 w-3", i < skill.level ? "bg-accent" : "bg-muted")}
                    />
                  ))}
                </span>
                <span className="text-right font-mono text-xs text-muted-foreground">
                  {skill.yearsOfExperience ? (
                    <>
                      {skill.yearsOfExperience}
                      <span className="sr-only"> years</span>
                      <span aria-hidden="true">y</span>
                    </>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
