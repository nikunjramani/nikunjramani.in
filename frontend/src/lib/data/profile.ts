import "server-only";

import { cache } from "react";

import { API_ROUTES } from "@/generated/api-routes";
import type { Profile } from "@/generated/types";

import { getPublic, type WithId } from "./api";

/** Null until the profile is saved and public — the API 404s otherwise. */
export const getProfile = cache(
  (): Promise<WithId<Profile> | null> => getPublic<Profile>(API_ROUTES.content.profile),
);
