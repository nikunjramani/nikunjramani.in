"use client";

import { useState } from "react";
import { useFormContext } from "react-hook-form";

import { Markdown } from "@/components/site/markdown";
import { cn } from "@/lib/utils";
import type { ResolvedField } from "./resolve-field";

/** No rich-text WYSIWYG, per the plan's own scope-creep warning — Markdown in a textarea
 * with a preview toggle, reusing the real public-site Markdown renderer so the preview is
 * never a second implementation that can drift from what actually publishes. */
export function MarkdownField({ name, field }: { name: string; field: ResolvedField }) {
  const { register, watch } = useFormContext();
  const [showPreview, setShowPreview] = useState(false);
  const value: string = watch(name) ?? "";

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <label htmlFor={name} className="text-sm font-medium">
          {field.key.charAt(0).toUpperCase() + field.key.slice(1)}
          {field.required ? <span className="text-accent"> *</span> : null}
        </label>
        <button
          type="button"
          onClick={() => setShowPreview((v) => !v)}
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          {showPreview ? "Edit" : "Preview"}
        </button>
      </div>
      {field.schema.description ? (
        <p className="text-xs text-muted-foreground">{field.schema.description}</p>
      ) : null}
      {showPreview ? (
        <div className="min-h-32 rounded-md border border-border bg-surface px-3 py-2">
          {value ? <Markdown>{value}</Markdown> : <p className="text-sm text-muted-foreground">Nothing yet.</p>}
        </div>
      ) : (
        <textarea
          id={name}
          rows={8}
          className={cn(
            "rounded-md border border-border bg-background px-3 py-2 font-mono text-sm focus-visible:outline-2 focus-visible:outline-accent",
          )}
          {...register(name)}
        />
      )}
    </div>
  );
}
