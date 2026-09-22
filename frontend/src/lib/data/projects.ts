import "server-only";

import { unstable_cache } from "next/cache";

import { db } from "@/lib/firebase/admin";
import type { Project } from "@/generated/types";

import { fromSnapshot, type WithId } from "./convert";

/**
 * `client.confidential: true` means the client's name must never reach the browser —
 * stripped here, not in a component. A component-level check still ships the value in
 * the RSC payload (React serialises props to the client regardless of what actually
 * renders), so this is the one place in the whole read path that can make that guarantee.
 * See CLAUDE.md's conventions and ADR 0008.
 */
function stripConfidentialClient(project: WithId<Project>): WithId<Project> {
  if (!project.client?.confidential) return project;
  const client = { ...project.client };
  delete client.name;
  return { ...project, client };
}

export const getFeaturedProjects = unstable_cache(
  async (): Promise<WithId<Project>[]> => {
    const snap = await db()
      .collection("projects")
      .where("visibility", "==", "public")
      .where("featured", "==", true)
      .orderBy("order")
      .get();
    return snap.docs
      .map((doc) => fromSnapshot<Project>(doc))
      .filter((doc): doc is WithId<Project> => doc !== null)
      .map(stripConfidentialClient);
  },
  ["projects-featured"],
  { tags: ["projects"], revalidate: 3600 },
);

export const getAllProjects = unstable_cache(
  async (): Promise<WithId<Project>[]> => {
    const snap = await db()
      .collection("projects")
      .where("visibility", "==", "public")
      .orderBy("order")
      .get();
    return snap.docs
      .map((doc) => fromSnapshot<Project>(doc))
      .filter((doc): doc is WithId<Project> => doc !== null)
      .map(stripConfidentialClient);
  },
  ["projects-all"],
  { tags: ["projects"], revalidate: 3600 },
);

export const getProjectBySlug = unstable_cache(
  async (slug: string): Promise<WithId<Project> | null> => {
    const snap = await db().collection("projects").doc(slug).get();
    const project = fromSnapshot<Project>(snap);
    // A visitor guessing a draft's slug must see a 404, not a preview.
    if (!project || project.visibility !== "public") return null;
    return stripConfidentialClient(project);
  },
  ["project-by-slug"],
  { tags: ["projects"], revalidate: 3600 },
);
