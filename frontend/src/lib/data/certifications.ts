import "server-only";

import { cache } from "react";

import { API_ROUTES } from "@/generated/api-routes";
import type { Certification } from "@/generated/types";

import { listPublic, type WithId } from "./api";

export const getCertifications = cache(
  (): Promise<WithId<Certification>[]> => listPublic<Certification>(API_ROUTES.content.certifications),
);
