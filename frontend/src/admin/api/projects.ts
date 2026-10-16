"use client";

import { API_ROUTES } from "@/generated/api-routes";
import type { Project } from "@/generated/types";
import { apiFetch } from "@/admin/api/client";
import type { RecordOut } from "@/admin/api/content";

export function duplicateProject(id: string): Promise<RecordOut<Project>> {
  return apiFetch(`/${API_ROUTES.content.projects}/${encodeURIComponent(id)}/duplicate`, {
    method: "POST",
  });
}
