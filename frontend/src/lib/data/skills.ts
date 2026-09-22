import "server-only";

import { unstable_cache } from "next/cache";

import type { Skill } from "@/generated/types";

import { listPublished } from "./shared";
import type { WithId } from "./convert";

export const getSkills = unstable_cache(
  (): Promise<WithId<Skill>[]> => listPublished<Skill>("skills"),
  ["skills-all"],
  { tags: ["skills"], revalidate: 3600 },
);

/** Skills are a small, admin-panel-loads-it-whole collection (BaseRepository's own
 * description of list_all) — filtering in memory rather than a second Firestore query. */
export async function getFeaturedSkills(): Promise<WithId<Skill>[]> {
  const skills = await getSkills();
  return skills.filter((skill) => skill.featured);
}
