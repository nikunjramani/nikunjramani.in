"use client";

import { ContentCollectionScreen } from "@/components/admin/content-collection-screen";
import { ADMIN_SCHEMAS } from "@/generated/admin-schemas";
import { CertificationSchema } from "@/generated/schemas.zod";

export default function AdminCertificationsPage() {
  return (
    <ContentCollectionScreen
      entry={ADMIN_SCHEMAS.Certification}
      zodSchema={CertificationSchema}
      title="Certification"
    />
  );
}
