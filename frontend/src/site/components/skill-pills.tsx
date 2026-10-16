import type { Skill } from "@/generated/types";
import type { WithId } from "@/lib/data/convert";

export function SkillPills({ skills }: { skills: WithId<Skill>[] }) {
  return (
    <ul className="flex flex-wrap gap-2">
      {skills.map((skill) => (
        <li
          key={skill.id}
          className="rounded-full border border-border bg-surface px-3 py-1.5 text-sm"
          title={skill.blurb}
        >
          {skill.name}
        </li>
      ))}
    </ul>
  );
}
