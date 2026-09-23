"use client";

import { ContentCollectionScreen } from "@/components/admin/content-collection-screen";
import { ADMIN_SCHEMAS } from "@/generated/admin-schemas";
import { ExperienceSchema } from "@/generated/schemas.zod";

export default function AdminExperiencePage() {
  return <ContentCollectionScreen entry={ADMIN_SCHEMAS.Experience} zodSchema={ExperienceSchema} title="Experience" />;
}
