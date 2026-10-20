import "server-only";

import { cache } from "react";

import { API_ROUTES } from "@/generated/api-routes";
import type { Experience } from "@/generated/types";

import { listPublic, type WithId } from "./api";

export const getExperience = cache(
  (): Promise<WithId<Experience>[]> => listPublic<Experience>(API_ROUTES.content.experience),
);
