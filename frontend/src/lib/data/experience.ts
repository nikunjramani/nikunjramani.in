import "server-only";

import { unstable_cache } from "next/cache";

import type { Experience } from "@/generated/types";

import type { WithId } from "./convert";
import { listPublished } from "./shared";

export const getExperience = unstable_cache(
  (): Promise<WithId<Experience>[]> => listPublished<Experience>("experience"),
  ["experience-all"],
  { tags: ["experience"], revalidate: 3600 },
);
