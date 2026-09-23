"use client";

import { useState } from "react";
import { useFormContext } from "react-hook-form";

import { cn } from "@/lib/utils";
import type { ResolvedField } from "./resolve-field";

function fieldLabel(key: string): string {
  const spaced = key.replace(/([A-Z])/g, " $1");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

function errorAt(errors: Record<string, unknown>, path: string): string | undefined {
  const parts = path.split(".");
  let node: unknown = errors;
  for (const part of parts) {
    if (!node || typeof node !== "object") return undefined;
    node = (node as Record<string, unknown>)[part];
  }
  if (node && typeof node === "object" && "message" in node) {
    const message = (node as { message?: unknown }).message;
    return typeof message === "string" ? message : undefined;
  }
  return undefined;
}

const inputClass =
  "rounded-md border border-border bg-background px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-accent";

function FieldShell({
  name,
  field,
  children,
}: {
  name: string;
  field: ResolvedField;
  children: React.ReactNode;
}) {
  const {
    formState: { errors },
  } = useFormContext();
  const message = errorAt(errors, name);

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={name} className="text-sm font-medium">
        {fieldLabel(field.key)}
        {field.required ? <span className="text-accent"> *</span> : null}
      </label>
      {field.schema.description ? (
        <p className="text-xs text-muted-foreground">{field.schema.description}</p>
      ) : null}
      {children}
      {message ? <p className="text-xs text-red-500">{message}</p> : null}
    </div>
  );
}

export function TextField({ name, field }: { name: string; field: ResolvedField }) {
  const { register } = useFormContext();
  return (
    <FieldShell name={name} field={field}>
      <input id={name} type="text" className={inputClass} {...register(name)} />
    </FieldShell>
  );
}

// A Zod format validator (.url(), .datetime(), .regex(...)) runs on whatever string is
// there before `.optional()` gets a say — an untouched HTML input's value is "", not
// undefined, so an empty *optional* formatted field fails validation as "invalid url" (or
// similar) instead of being treated as simply not filled in. Same underlying issue as
// NumberField's NaN case, different shape.
function emptyToUndefined(value: string): string | undefined {
  return value === "" ? undefined : value;
}

export function UrlField({ name, field }: { name: string; field: ResolvedField }) {
  const { register } = useFormContext();
  return (
    <FieldShell name={name} field={field}>
      <input
        id={name}
        type="url"
        className={inputClass}
        {...register(name, { setValueAs: emptyToUndefined })}
      />
    </FieldShell>
  );
}

export function MonthField({ name, field }: { name: string; field: ResolvedField }) {
  const { register } = useFormContext();
  return (
    <FieldShell name={name} field={field}>
      <input
        id={name}
        type="text"
        placeholder="YYYY-MM"
        className={inputClass}
        {...register(name, { setValueAs: emptyToUndefined })}
      />
    </FieldShell>
  );
}

export function DateField({ name, field }: { name: string; field: ResolvedField }) {
  const { register } = useFormContext();
  return (
    <FieldShell name={name} field={field}>
      <input
        id={name}
        type="datetime-local"
        className={inputClass}
        {...register(name, { setValueAs: emptyToUndefined })}
      />
    </FieldShell>
  );
}

export function TextareaField({ name, field }: { name: string; field: ResolvedField }) {
  const { register } = useFormContext();
  return (
    <FieldShell name={name} field={field}>
      <textarea id={name} rows={4} className={inputClass} {...register(name)} />
    </FieldShell>
  );
}

export function NumberField({ name, field }: { name: string; field: ResolvedField }) {
  const { register } = useFormContext();
  const schema = field.schema;
  return (
    <FieldShell name={name} field={field}>
      <input
        id={name}
        type="number"
        min={schema.minimum}
        max={schema.maximum}
        step={schema.type === "integer" ? 1 : "any"}
        className={cn(inputClass, "w-40")}
        {...register(name, {
          // valueAsNumber: true turns an emptied, optional field into NaN (Number("") is
          // NaN, not undefined) — Zod's `.optional()` rejects NaN outright, so clearing an
          // optional number field made the form permanently unsubmittable. An explicit
          // setValueAs is the only way to get "empty means absent" instead.
          setValueAs: (value: string) => (value === "" ? undefined : Number(value)),
        })}
      />
    </FieldShell>
  );
}

export function BooleanField({ name, field }: { name: string; field: ResolvedField }) {
  const { register } = useFormContext();
  return (
    <div className="flex items-center gap-2.5">
      <input id={name} type="checkbox" className="h-4 w-4 accent-accent" {...register(name)} />
      <label htmlFor={name} className="text-sm font-medium">
        {fieldLabel(field.key)}
      </label>
      {field.schema.description ? (
        <span className="text-xs text-muted-foreground">— {field.schema.description}</span>
      ) : null}
    </div>
  );
}

export function SelectField({ name, field }: { name: string; field: ResolvedField }) {
  const { register } = useFormContext();
  const options = (field.schema.enum ?? []) as string[];
  return (
    <FieldShell name={name} field={field}>
      <select id={name} className={inputClass} {...register(name)}>
        {!field.required ? <option value="">—</option> : null}
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </FieldShell>
  );
}

export function TagsField({ name, field }: { name: string; field: ResolvedField }) {
  const { watch, setValue } = useFormContext();
  const [draft, setDraft] = useState("");
  const tags: string[] = watch(name) ?? [];

  function addTag() {
    const value = draft.trim();
    if (!value || tags.includes(value)) return;
    setValue(name, [...tags, value], { shouldDirty: true });
    setDraft("");
  }

  function removeTag(tag: string) {
    setValue(
      name,
      tags.filter((t) => t !== tag),
      { shouldDirty: true },
    );
  }

  return (
    <FieldShell name={name} field={field}>
      <div className="flex flex-wrap gap-1.5">
        {tags.map((tag) => (
          <span
            key={tag}
            className="flex items-center gap-1 rounded-full bg-muted px-2.5 py-1 text-xs"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(tag)}
              aria-label={`Remove ${tag}`}
              className="text-muted-foreground hover:text-foreground"
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addTag();
            }
          }}
          className={cn(inputClass, "flex-1")}
          placeholder="Add and press Enter"
        />
        <button
          type="button"
          onClick={addTag}
          className="rounded-md border border-border px-3 py-2 text-sm hover:bg-muted"
        >
          Add
        </button>
      </div>
    </FieldShell>
  );
}
