"use client";

import { ContentCollectionScreen } from "@/components/admin/content-collection-screen";
import { ADMIN_SCHEMAS } from "@/generated/admin-schemas";
import { SkillSchema } from "@/generated/schemas.zod";

export default function AdminSkillsPage() {
  return (
    <ContentCollectionScreen
      entry={ADMIN_SCHEMAS.Skill}
      zodSchema={SkillSchema}
      title="Skill"
      groupBy="category"
    />
  );
}
