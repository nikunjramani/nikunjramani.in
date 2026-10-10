"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { FormProvider, useForm } from "react-hook-form";
import type { z } from "zod";

import { FieldRenderer } from "./field-renderer";
import { formFieldEntries } from "./resolve-field";
import type { AdminSchemaEntry } from "@/generated/admin-schemas";

const DRAFT_PREFIX = "admin-draft:";

interface StoredDraft {
  values: unknown;
  savedAt: number;
}

function loadDraft(key: string): StoredDraft | null {
  try {
    const raw = localStorage.getItem(DRAFT_PREFIX + key);
    if (!raw) return null;
    return JSON.parse(raw) as StoredDraft;
  } catch {
    return null;
  }
}

function saveDraft(key: string, values: unknown): void {
  try {
    localStorage.setItem(DRAFT_PREFIX + key, JSON.stringify({ values, savedAt: Date.now() }));
  } catch {
    // localStorage can throw (private mode, quota) — losing autosave silently beats
    // breaking the form over a convenience feature.
  }
}

function clearDraft(key: string): void {
  try {
    localStorage.removeItem(DRAFT_PREFIX + key);
  } catch {
    // see saveDraft
  }
}

function timeAgo(ms: number): string {
  const minutes = Math.round((Date.now() - ms) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.round(minutes / 60)}h ago`;
}

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
  /** Fires on every keystroke with the current (possibly invalid, possibly unsaved) form
   * state — the project editor's live preview subscribes to this rather than SchemaForm
   * needing any preview-specific concept of its own. */
  onValuesChange?: (values: z.infer<T>) => void;
  /** Enables autosave-to-localStorage (5.7) when set — one key per document being edited,
   * e.g. `projects:${id}` or `projects:new` for a not-yet-created one. Left unset, the form
   * behaves exactly as before with no draft persistence. */
  autosaveKey?: string;
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
  onValuesChange,
  autosaveKey,
}: SchemaFormProps<T>) {
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Starts null on *every* render, server or client — reading localStorage inside a
  // useState initializer would run during SSR too (Client Components still render once on
  // the server for the initial HTML), where localStorage doesn't exist, so the found-a-
  // draft branch would only ever show up after hydration and React would flag the
  // mismatch. Checking inside an effect means this never runs until the client is already
  // the only one rendering, at the cost of the banner (and the draft values themselves)
  // appearing one tick after first paint instead of being there immediately — a fine trade
  // for a convenience feature nobody is staring at the instant the page loads.
  const [initialDraft, setInitialDraft] = useState<StoredDraft | null>(null);
  const [draftBannerDismissed, setDraftBannerDismissed] = useState(false);
  const [fieldTreeKey, setFieldTreeKey] = useState(0);

  const form = useForm<z.infer<T>>({
    resolver: zodResolver(zodSchema),
    defaultValues: nullsToUndefined(defaultValues),
  });

  const { isDirty } = form.formState;

  useEffect(() => {
    if (!autosaveKey) return;
    const draft = loadDraft(autosaveKey);
    if (!draft) return;
    setInitialDraft(draft);
    form.reset(nullsToUndefined(draft.values as z.infer<T>));
    // Runs once on mount to check for a pre-existing draft — form.reset intentionally
    // isn't a dependency (react-hook-form's own instance is stable per SchemaForm mount).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autosaveKey]);

  useEffect(() => {
    const subscription = form.watch((values) => {
      onValuesChange?.(values as z.infer<T>);
    });
    return () => subscription.unsubscribe();
    // form.watch's callback identity doesn't need to be a dependency — react-hook-form's
    // own subscription object is stable across renders.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form]);

  // Autosave: debounced so every keystroke doesn't hit localStorage, cleared on a
  // successful save (the server copy is now authoritative, so a stale local draft left
  // behind would only ever cause confusion, not help).
  useEffect(() => {
    if (!autosaveKey) return;
    let timeout: ReturnType<typeof setTimeout>;
    const subscription = form.watch((values) => {
      clearTimeout(timeout);
      // Not just a micro-optimization: reset() (discarding a draft, or a successful save)
      // itself fires this same watch callback, and without this guard the debounced save
      // scheduled from *before* the reset would still land afterward and silently recreate
      // the draft it was just asked to clear.
      if (!form.formState.isDirty) return;
      timeout = setTimeout(() => saveDraft(autosaveKey, values), 1000);
    });
    return () => {
      clearTimeout(timeout);
      subscription.unsubscribe();
    };
  }, [form, autosaveKey]);

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
      if (autosaveKey) clearDraft(autosaveKey);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSaving(false);
    }
  }

  function discardDraft() {
    if (!autosaveKey) return;
    clearDraft(autosaveKey);
    form.reset(nullsToUndefined(defaultValues));
    // form.reset() alone leaves uncontrolled inputs showing their old DOM value in this
    // nested-FormProvider setup — react-hook-form's internal state (getValues()) comes back
    // correctly empty, but the native <input> element it registered earlier doesn't get its
    // .value imperatively cleared. Remounting the whole field tree sidesteps the discrepancy
    // outright: every control re-registers from scratch against the now-reset form values.
    setFieldTreeKey((k) => k + 1);
    setDraftBannerDismissed(true);
  }

  return (
    <FormProvider {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="flex flex-col gap-6" noValidate>
        {initialDraft && !draftBannerDismissed ? (
          <div className="flex items-center justify-between gap-3 rounded-md border border-accent/40 bg-accent/5 px-4 py-2.5 text-sm">
            <span>Restored an unsaved draft from {timeAgo(initialDraft.savedAt)}.</span>
            <button
              type="button"
              onClick={discardDraft}
              className="shrink-0 text-xs text-muted-foreground underline hover:text-foreground"
            >
              Discard, use last saved version
            </button>
          </div>
        ) : null}

        <div key={fieldTreeKey} className="contents">
          {fields.map((field) => (
            <FieldRenderer key={field.key} name={field.key} field={field} />
          ))}
        </div>

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
