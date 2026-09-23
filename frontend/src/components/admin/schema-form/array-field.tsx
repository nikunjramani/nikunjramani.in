"use client";

import { ChevronDown, ChevronUp, Plus, Trash2 } from "lucide-react";
import { useFieldArray, useFormContext } from "react-hook-form";
import type { JSONSchema7 } from "json-schema";

import { formFieldEntries } from "./resolve-field";
import type { ResolvedField } from "./resolve-field";
import { FieldRenderer } from "./field-renderer";

function sectionLabel(key: string): string {
  const spaced = key.replace(/([A-Z])/g, " $1");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

/** Add, remove, reorder — with useFieldArray's own stable `id` as the React key, never the
 * array index. An index-based key scrambles form state the instant an item moves, since
 * React then reuses the wrong DOM node's uncontrolled state for the new item at that index —
 * exactly the trap the plan's own gotchas call out. */
export function ArrayOfObjectsField({ name, field }: { name: string; field: ResolvedField }) {
  const { control } = useFormContext();
  const { fields, append, remove, move } = useFieldArray({ control, name });

  const itemSchemaRaw = field.schema.items;
  const itemSchema = (Array.isArray(itemSchemaRaw) ? itemSchemaRaw[0] : itemSchemaRaw) as
    | JSONSchema7
    | undefined;
  const properties = (itemSchema?.properties ?? {}) as Record<string, JSONSchema7>;
  const required = itemSchema?.required ?? [];
  const itemFields = formFieldEntries(properties, required);
  const maxItems = field.schema.maxItems;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">
          {sectionLabel(field.key)}
          {field.required ? <span className="text-accent"> *</span> : null}
        </span>
        <button
          type="button"
          onClick={() => append({})}
          disabled={maxItems !== undefined && fields.length >= maxItems}
          className="inline-flex items-center gap-1 text-xs text-accent hover:underline disabled:cursor-not-allowed disabled:opacity-50 disabled:no-underline"
        >
          <Plus className="h-3.5 w-3.5" aria-hidden="true" />
          Add
        </button>
      </div>
      {field.schema.description ? (
        <p className="-mt-2 text-xs text-muted-foreground">{field.schema.description}</p>
      ) : null}

      {fields.length === 0 ? (
        <p className="text-sm text-muted-foreground">None yet.</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {fields.map((item, index) => (
            <li key={item.id} className="flex flex-col gap-3 rounded-lg border border-border p-4">
              <div className="flex items-center justify-end gap-1">
                <button
                  type="button"
                  onClick={() => move(index, index - 1)}
                  disabled={index === 0}
                  aria-label="Move up"
                  className="rounded p-1 text-muted-foreground hover:text-foreground disabled:opacity-30"
                >
                  <ChevronUp className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => move(index, index + 1)}
                  disabled={index === fields.length - 1}
                  aria-label="Move down"
                  className="rounded p-1 text-muted-foreground hover:text-foreground disabled:opacity-30"
                >
                  <ChevronDown className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => remove(index)}
                  aria-label="Remove"
                  className="rounded p-1 text-muted-foreground hover:text-red-500"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
              <div className="flex flex-col gap-4">
                {itemFields.map((child) => (
                  <FieldRenderer key={child.key} name={`${name}.${index}.${child.key}`} field={child} />
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
