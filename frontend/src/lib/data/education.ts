import "server-only";

import { unstable_cache } from "next/cache";

import type { Education } from "@/generated/types";

import { listPublished } from "./shared";
import type { WithId } from "./convert";

export const getEducations = unstable_cache(
  (): Promise<WithId<Education>[]> => listPublished<Education>("education"),
  ["education-all"],
  { tags: ["education"], revalidate: 3600 },
);
