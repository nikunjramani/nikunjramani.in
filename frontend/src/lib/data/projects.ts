import "server-only";

import { cache } from "react";

import { API_ROUTES } from "@/generated/api-routes";
import type { Project } from "@/generated/types";

import { getPublic, listPublic, type WithId } from "./api";

// Visibility and a confidential client's name and logo are handled by the API
// (ProjectService), so nothing that must not reach the browser ever arrives here.

/** `public` projects only — listings, the sitemap and prev/next never include `unlisted`. */
export const getAllProjects = cache(
  (): Promise<WithId<Project>[]> => listPublic<Project>(API_ROUTES.content.projects),
);

export const getFeaturedProjects = cache(async (): Promise<WithId<Project>[]> =>
  (await getAllProjects()).filter((project) => project.featured),
);

/** A project page: `public` or `unlisted`; null (a 404) for a draft or an unknown slug. */
export const getProjectBySlug = cache(
  (slug: string): Promise<WithId<Project> | null> =>
    getPublic<Project>(API_ROUTES.content.projects, slug),
);
