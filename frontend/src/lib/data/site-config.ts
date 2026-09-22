import "server-only";

import { unstable_cache } from "next/cache";

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

export const getSiteConfig = unstable_cache(
  async (): Promise<WithId<SiteConfig>> => {
    const snap = await db().collection("site_config").doc("main").get();
    return fromSnapshot<SiteConfig>(snap) ?? DEFAULTS;
  },
  ["site-config-main"],
  { tags: ["site_config"], revalidate: 3600 },
);
