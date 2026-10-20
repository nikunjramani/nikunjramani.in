import "server-only";

import { cache } from "react";

import { API_ROUTES } from "@/generated/api-routes";
import type { SiteConfig } from "@/generated/types";

import { getPublic, type WithId } from "./api";

const DEFAULTS: WithId<SiteConfig> = {
  id: "main",
  visibility: "public",
  showBlog: false,
  showTestimonials: false,
  maintenanceMode: false,
};

export const getSiteConfig = cache(
  async (): Promise<WithId<SiteConfig>> =>
    (await getPublic<SiteConfig>(API_ROUTES.content.settings)) ?? DEFAULTS,
);
