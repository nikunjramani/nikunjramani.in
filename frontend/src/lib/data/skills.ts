import "server-only";

import { cache } from "react";

import { API_ROUTES } from "@/generated/api-routes";
import type { Skill } from "@/generated/types";

import { listPublic, type WithId } from "./api";

export const getSkills = cache(
  (): Promise<WithId<Skill>[]> => listPublic<Skill>(API_ROUTES.content.skills),
);

/** Skills are a small collection — filtered here rather than a second API call. */
export async function getFeaturedSkills(): Promise<WithId<Skill>[]> {
  const skills = await getSkills();
  return skills.filter((skill) => skill.featured);
}
