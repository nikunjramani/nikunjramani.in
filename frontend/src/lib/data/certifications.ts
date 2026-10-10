import "server-only";

import { cache } from "react";

import type { Certification } from "@/generated/types";

import { listPublished } from "./shared";
import type { WithId } from "./convert";

export const getCertifications = cache(
  (): Promise<WithId<Certification>[]> => listPublished<Certification>("certifications"),
);
