"use client";

import { API_ROUTES } from "@/generated/api-routes";
import type { Project } from "@/generated/types";
import { apiFetch } from "@/lib/api/client";
import type { RecordOut } from "@/lib/api/content";

export function duplicateProject(id: string): Promise<RecordOut<Project>> {
  return apiFetch(`/${API_ROUTES.content.projects}/${encodeURIComponent(id)}/duplicate`, {
    method: "POST",
  });
}
