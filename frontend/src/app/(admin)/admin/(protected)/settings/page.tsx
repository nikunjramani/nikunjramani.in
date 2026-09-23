"use client";

import { SingletonScreen } from "@/components/admin/singleton-screen";
import { ADMIN_SCHEMAS } from "@/generated/admin-schemas";
import { SiteConfigSchema } from "@/generated/schemas.zod";

export default function AdminSettingsPage() {
  return <SingletonScreen entry={ADMIN_SCHEMAS.SiteConfig} zodSchema={SiteConfigSchema} title="Settings" />;
}
