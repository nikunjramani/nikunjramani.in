import "server-only";

import { cache } from "react";

import type { Experience } from "@/generated/types";

import type { WithId } from "./convert";
import { listPublished } from "./shared";

export const getExperience = cache(
  (): Promise<WithId<Experience>[]> => listPublished<Experience>("experience"),
);
