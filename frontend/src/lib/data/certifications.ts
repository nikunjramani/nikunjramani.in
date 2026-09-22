import "server-only";

import { unstable_cache } from "next/cache";

import type { Certification } from "@/generated/types";

import { listPublished } from "./shared";
import type { WithId } from "./convert";

export const getCertifications = unstable_cache(
  (): Promise<WithId<Certification>[]> => listPublished<Certification>("certifications"),
  ["certifications-all"],
  { tags: ["certifications"], revalidate: 3600 },
);
