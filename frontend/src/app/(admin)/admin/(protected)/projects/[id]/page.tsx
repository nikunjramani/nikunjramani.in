"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AuditTrail } from "@/components/admin/audit-trail";
import { SchemaForm } from "@/components/admin/schema-form/schema-form";
import { useFeedback } from "@/components/admin/ui-feedback";
import { ProjectDetailView } from "@/components/site/project/project-detail-view";
import { ADMIN_SCHEMAS } from "@/generated/admin-schemas";
import { ProjectSchema } from "@/generated/schemas.zod";
import type { Project } from "@/generated/types";
import type { z } from "zod";

type ProjectFormValues = z.infer<typeof ProjectSchema>;
import { ApiError } from "@/lib/api/client";
import { createRecord, getRecord, patchRecord } from "@/lib/api/content";

const entry = ADMIN_SCHEMAS.Project;
const EMPTY_PROJECT = {} as Project;

export default function AdminProjectEditorPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { toast } = useFeedback();
  const isNew = params.id === "new";

  const [record, setRecord] = useState<Project | null>(isNew ? EMPTY_PROJECT : null);
  const [notFound, setNotFound] = useState(false);
  const [preview, setPreview] = useState<Project>(EMPTY_PROJECT);

  useEffect(() => {
    if (isNew) return;
    getRecord<Project>(entry.apiDomain, params.id)
      .then((r) => {
        setRecord(r.data);
        setPreview(r.data);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) setNotFound(true);
      });
  }, [isNew, params.id]);

  async function handleCreate(values: ProjectFormValues) {
    const created = await createRecord<Project>(entry.apiDomain, values);
    toast("Project created.");
    router.replace(`/admin/projects/${created.id}`);
  }

  async function handleUpdate(values: ProjectFormValues) {
    await patchRecord(entry.apiDomain, params.id, values as unknown as Record<string, unknown>);
    toast("Project saved.");
  }

  if (notFound) {
    return <p className="text-sm text-muted-foreground">No project found at this id.</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">{isNew ? "New project" : record?.title}</h1>
        {!isNew && record ? (
          <span className="rounded-full border border-border px-2.5 py-0.5 text-xs text-muted-foreground">
            {record.visibility === "public" ? "Published" : record.visibility}
          </span>
        ) : null}
      </div>

      {record === null ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <div className="flex flex-col gap-6">
            <SchemaForm
              entry={entry}
              zodSchema={ProjectSchema}
              defaultValues={record as ProjectFormValues}
              onSubmit={isNew ? handleCreate : handleUpdate}
              onValuesChange={(values) => setPreview(values as unknown as Project)}
              submitLabel={isNew ? "Create" : "Save"}
            />
            {!isNew ? <AuditTrail collection="projects" docId={params.id} /> : null}
          </div>

          <div className="lg:sticky lg:top-6 lg:self-start">
            <p className="mb-3 text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Live preview
            </p>
            <div className="max-h-[85vh] overflow-y-auto rounded-lg border border-border bg-background p-6">
              <ProjectDetailView project={preview} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
