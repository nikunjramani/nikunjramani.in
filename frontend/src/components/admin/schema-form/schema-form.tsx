"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { FormProvider, useForm } from "react-hook-form";
import type { z } from "zod";

import { FieldRenderer } from "./field-renderer";
import { formFieldEntries } from "./resolve-field";
import type { AdminSchemaEntry } from "@/generated/admin-schemas";

/**
 * FastAPI serializes an unset Optional field as JSON `null` by default (Pydantic's
 * `exclude_none` isn't set on these response models) — but the generated Zod schemas use
 * `.optional()`, which accepts `undefined` and rejects `null` outright. Loading a real
 * record straight off the API as `defaultValues` therefore fails validation on every
 * untouched optional field the instant the form is submitted, even with no edits made to
 * that field. Converting null -> undefined here, once, covers every caller rather than
 * requiring each one to remember to sanitize its own data before handing it to the form.
 */
function nullsToUndefined<T>(value: T): T {
  if (value === null) return undefined as T;
  if (Array.isArray(value)) return value.map(nullsToUndefined) as T;
  if (typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([k, v]) => [k, nullsToUndefined(v)]),
    ) as T;
  }
  return value;
}

export interface SchemaFormProps<T extends z.ZodTypeAny> {
  entry: AdminSchemaEntry;
  zodSchema: T;
  defaultValues: z.infer<T>;
  onSubmit: (values: z.infer<T>) => Promise<void>;
  submitLabel?: string;
}

/**
 * The centrepiece: reads entry.properties (a dereferenced JSON Schema, generated straight
 * from architecture/schemas — see gen-frontend.mjs) and renders the whole form from it,
 * validated against the matching generated Zod schema. Adding a field to a schema and
 * running `make gen` makes it appear here with zero changes to this file or any of the
 * field-kind components — that's the plan's own "test 6".
 */
export function SchemaForm<T extends z.ZodTypeAny>({
  entry,
  zodSchema,
  defaultValues,
  onSubmit,
  submitLabel = "Save",
}: SchemaFormProps<T>) {
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const form = useForm<z.infer<T>>({
    resolver: zodResolver(zodSchema),
    defaultValues: nullsToUndefined(defaultValues),
  });

  const { isDirty } = form.formState;

  // Unsaved-changes guard: a tab close or refresh with unsaved edits gets a native confirm
  // prompt. App Router has no built-in way to intercept an in-app Link navigation the way
  // Pages Router's routeChangeStart did, so this covers the case that's both the easiest to
  // lose work to (an accidental refresh) and the only one a generic hook can cover safely.
  useEffect(() => {
    if (!isDirty) return;
    function onBeforeUnload(e: BeforeUnloadEvent) {
      e.preventDefault();
    }
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [isDirty]);

  const fields = formFieldEntries(entry.properties, entry.required);

  async function handleSubmit(values: z.infer<T>) {
    setSaving(true);
    setSaveError(null);
    try {
      await onSubmit(values);
      form.reset(values);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="flex flex-col gap-6" noValidate>
        {fields.map((field) => (
          <FieldRenderer key={field.key} name={field.key} field={field} />
        ))}

        {saveError ? <p className="text-sm text-red-500">{saveError}</p> : null}

        <div className="flex items-center gap-3 border-t border-border pt-4">
          <button
            type="submit"
            disabled={saving || !isDirty}
            className="inline-flex items-center gap-1.5 rounded-md bg-accent px-4 py-2 text-sm text-accent-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {submitLabel}
          </button>
          {isDirty ? <span className="text-xs text-muted-foreground">Unsaved changes</span> : null}
        </div>
      </form>
    </FormProvider>
  );
}
