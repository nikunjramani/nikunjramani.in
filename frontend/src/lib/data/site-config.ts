import "server-only";

import { cache } from "react";

import { db } from "@/lib/firebase/admin";
import type { SiteConfig } from "@/generated/types";

import { fromSnapshot, type WithId } from "./convert";

const DEFAULTS: WithId<SiteConfig> = {
  id: "main",
  visibility: "public",
  showBlog: false,
  showTestimonials: false,
  maintenanceMode: false,
};

export const getSiteConfig = cache(
  async (): Promise<WithId<SiteConfig>> => {
    const snap = await db().collection("site_config").doc("main").get();
    const config = fromSnapshot<SiteConfig>(snap);
    return config?.visibility === "public" ? config : DEFAULTS;
  },
);
