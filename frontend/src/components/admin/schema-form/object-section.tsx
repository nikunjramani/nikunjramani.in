"use client";

import { ChevronDown, ChevronRight, Plus, X } from "lucide-react";
import { useState } from "react";
import { useFormContext } from "react-hook-form";
import type { JSONSchema7 } from "json-schema";

import { formFieldEntries } from "./resolve-field";
import type { ResolvedField } from "./resolve-field";
import { FieldRenderer } from "./field-renderer";

function hasAnyValue(value: unknown): boolean {
  if (value === undefined || value === null) return false;
  if (typeof value === "object") {
    return Object.values(value as Record<string, unknown>).some((v) => hasAnyValue(v));
  }
  if (Array.isArray(value)) return value.length > 0;
  return value !== "" && value !== false;
}

/** Optional nested objects (team, client, testimonial, content.architecture, …) collapse by
 * default with an "add a section" affordance — the plan's own words — rather than showing
 * every optional block expanded, which is what turns a 6-required-field schema into what
 * feels like a 40-field wall. */
export function ObjectSection({ name, field }: { name: string; field: ResolvedField }) {
  const { watch, setValue } = useFormContext();
  const currentValue = watch(name);
  const [expanded, setExpanded] = useState(field.required || hasAnyValue(currentValue));

  const properties = (field.schema.properties ?? {}) as Record<string, JSONSchema7>;
  const required = field.schema.required ?? [];
  const children = formFieldEntries(properties, required);

  if (!expanded) {
    return (
      <button
        type="button"
        onClick={() => setExpanded(true)}
        className="flex items-center gap-1.5 rounded-md border border-dashed border-border px-3 py-2 text-sm text-muted-foreground hover:border-accent hover:text-accent"
      >
        <Plus className="h-3.5 w-3.5" aria-hidden="true" />
        Add {sectionLabel(field.key)}
      </button>
    );
  }

  return (
    <fieldset className="flex flex-col gap-4 rounded-lg border border-border p-4">
      <legend className="flex w-full items-center justify-between px-1 text-sm font-medium">
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="flex items-center gap-1.5 hover:text-accent"
        >
          {expanded ? (
            <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
          )}
          {sectionLabel(field.key)}
        </button>
        {!field.required ? (
          <button
            type="button"
            onClick={() => {
              setValue(name, undefined, { shouldDirty: true });
              setExpanded(false);
            }}
            aria-label={`Remove ${sectionLabel(field.key)}`}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        ) : null}
      </legend>
      {field.schema.description ? (
        <p className="-mt-2 text-xs text-muted-foreground">{field.schema.description}</p>
      ) : null}
      <div className="flex flex-col gap-4">
        {children.map((child) => (
          <FieldRenderer key={child.key} name={`${name}.${child.key}`} field={child} />
        ))}
      </div>
    </fieldset>
  );
}

function sectionLabel(key: string): string {
  const spaced = key.replace(/([A-Z])/g, " $1");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}
