"use client";

import { ContentCollectionScreen } from "@/components/admin/content-collection-screen";
import { ADMIN_SCHEMAS } from "@/generated/admin-schemas";
import { EducationSchema } from "@/generated/schemas.zod";

export default function AdminEducationPage() {
  return <ContentCollectionScreen entry={ADMIN_SCHEMAS.Education} zodSchema={EducationSchema} title="Education" />;
}
