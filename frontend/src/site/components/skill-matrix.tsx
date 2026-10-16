import type { Skill } from "@/generated/types";
import type { WithId } from "@/lib/data/convert";

const CATEGORY_LABEL: Record<string, string> = {
  backend: "Backend",
  frontend: "Frontend",
  "cloud-devops": "Cloud & DevOps",
  data: "Data",
  mobile: "Mobile",
  tools: "Tools",
};

export function SkillMatrix({ skills }: { skills: WithId<Skill>[] }) {
  const byCategory = new Map<string, WithId<Skill>[]>();
  for (const skill of skills) {
    byCategory.set(skill.category, [...(byCategory.get(skill.category) ?? []), skill]);
  }

  return (
    <div className="flex flex-col gap-6">
      {[...byCategory.entries()].map(([category, categorySkills]) => (
        <div key={category}>
          <h3 className="mb-3 text-xs font-medium text-muted-foreground uppercase tracking-wide">
            {CATEGORY_LABEL[category] ?? category}
          </h3>
          <ul className="flex flex-col gap-2">
            {categorySkills.map((skill) => (
              <li key={skill.id} className="flex items-center gap-3" title={skill.blurb}>
                <span className="w-32 shrink-0 text-sm">{skill.name}</span>
                <span className="flex gap-1" aria-label={`Proficiency ${skill.level} of 5`}>
                  {Array.from({ length: 5 }, (_, i) => (
                    <span
                      key={i}
                      aria-hidden="true"
                      className={`h-1.5 w-4 rounded-full ${i < skill.level ? "bg-accent" : "bg-muted"}`}
                    />
                  ))}
                </span>
                {skill.yearsOfExperience ? (
                  <span className="text-xs text-muted-foreground">{skill.yearsOfExperience}y</span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
