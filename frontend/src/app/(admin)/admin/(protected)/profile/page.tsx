"use client";

import { SingletonScreen } from "@/components/admin/singleton-screen";
import { ADMIN_SCHEMAS } from "@/generated/admin-schemas";
import { ProfileSchema } from "@/generated/schemas.zod";

export default function AdminProfilePage() {
  return <SingletonScreen entry={ADMIN_SCHEMAS.Profile} zodSchema={ProfileSchema} title="Profile" />;
}
