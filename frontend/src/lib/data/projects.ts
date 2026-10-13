import "server-only";

import { cache } from "react";

import { db } from "@/lib/firebase/admin";
import type { Project } from "@/generated/types";

import { fromSnapshot, type WithId } from "./convert";
import { listPublished } from "./shared";

/**
 * `client.confidential: true` means nothing identifying the client may reach the browser —
 * neither the name nor the logo. Stripped here, not in a component: React serialises props
 * into the RSC payload regardless of what renders, so this is the one place in the read
 * path that can make the guarantee. See CLAUDE.md's conventions and ADR 0008.
 */
function stripConfidentialClient(project: WithId<Project>): WithId<Project> {
  if (!project.client?.confidential) return project;
  const client = { ...project.client };
  delete client.name;
  delete client.logoUrl;
  return { ...project, client };
}

export const getFeaturedProjects = cache(
  async (): Promise<WithId<Project>[]> =>
    (await listPublished<Project>("projects", { featured: true })).map(stripConfidentialClient),
);

export const getAllProjects = cache(
  async (): Promise<WithId<Project>[]> =>
    (await listPublished<Project>("projects")).map(stripConfidentialClient),
);

/** Visibility values a project page may be served for. `unlisted` is reachable by its URL
 * but never listed — getAllProjects (listings, sitemap, prev/next) only returns `public`. */
const REACHABLE_BY_URL = new Set(["public", "unlisted"]);

export const getProjectBySlug = cache(
  async (slug: string): Promise<WithId<Project> | null> => {
    const snap = await db().collection("projects").doc(slug).get();
    const project = fromSnapshot<Project>(snap);
    // A visitor guessing a draft's slug must see a 404, not a preview.
    if (!project || !REACHABLE_BY_URL.has(project.visibility)) return null;
    return stripConfidentialClient(project);
  },
);
