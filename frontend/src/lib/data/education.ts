import "server-only";

import { cache } from "react";

import { API_ROUTES } from "@/generated/api-routes";
import type { Education } from "@/generated/types";

import { listPublic, type WithId } from "./api";

export const getEducations = cache(
  (): Promise<WithId<Education>[]> => listPublic<Education>(API_ROUTES.content.education),
);
