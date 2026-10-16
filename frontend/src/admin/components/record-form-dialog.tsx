"use client";

import { X } from "lucide-react";
import type { z } from "zod";

import { AuditTrail } from "@/admin/components/audit-trail";
import { SchemaForm, type SchemaFormProps } from "@/admin/components/schema-form/schema-form";

export function RecordFormDialog<T extends z.ZodTypeAny>({
  title,
  onClose,
  auditTrail,
  ...schemaFormProps
}: SchemaFormProps<T> & {
  title: string;
  onClose: () => void;
  /** Omitted for a not-yet-created record — nothing to show history for yet. */
  auditTrail?: { collection: string; docId: string };
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      className="fixed inset-0 z-40 flex items-start justify-center overflow-y-auto bg-black/70 p-6"
      onClick={onClose}
    >
      <div
        className="my-8 flex w-full max-w-xl flex-col gap-5 rounded-lg border border-border bg-background p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="font-medium">{title}</h2>
          <button type="button" onClick={onClose} aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>
        <SchemaForm {...schemaFormProps} />
        {auditTrail ? <AuditTrail collection={auditTrail.collection} docId={auditTrail.docId} /> : null}
      </div>
    </div>
  );
}
