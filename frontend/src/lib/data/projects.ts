import "server-only";

import { cache } from "react";

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

export const getFeaturedProjects = cache(
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
);

export const getAllProjects = cache(
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
);

export const getProjectBySlug = cache(
  async (slug: string): Promise<WithId<Project> | null> => {
    const snap = await db().collection("projects").doc(slug).get();
    const project = fromSnapshot<Project>(snap);
    // A visitor guessing a draft's slug must see a 404, not a preview.
    if (!project || project.visibility !== "public") return null;
    return stripConfidentialClient(project);
  },
);
