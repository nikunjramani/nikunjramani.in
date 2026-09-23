"use client";

import { ImageOff, Plus, X } from "lucide-react";
import Image from "next/image";
import { useEffect, useState } from "react";
import { useFormContext } from "react-hook-form";

import { listRecords } from "@/lib/api/content";
import { cn } from "@/lib/utils";
import type { ResolvedField } from "./resolve-field";

interface MediaAssetLike {
  url: string;
  alt?: string;
  thumbnailUrl?: string;
}

const inputClass =
  "rounded-md border border-border bg-background px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-accent";

function LibraryDialog({
  onPick,
  onClose,
}: {
  onPick: (asset: MediaAssetLike) => void;
  onClose: () => void;
}) {
  const [assets, setAssets] = useState<{ id: string; data: MediaAssetLike }[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    listRecords<MediaAssetLike>("media")
      .then(setAssets)
      .catch(() => setError(true));
  }, []);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Media library"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-6"
      onClick={onClose}
    >
      <div
        className="flex max-h-[80vh] w-full max-w-2xl flex-col gap-4 overflow-y-auto rounded-lg border border-border bg-background p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="font-medium">Media library</h2>
          <button type="button" onClick={onClose} aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>
        {error ? (
          <p className="text-sm text-red-500">Couldn&apos;t load the media library.</p>
        ) : assets === null ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : assets.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No media uploaded yet — use the Media section to upload some first.
          </p>
        ) : (
          <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">
            {assets.map((asset) => (
              <button
                key={asset.id}
                type="button"
                onClick={() => onPick(asset.data)}
                disabled={!asset.data.alt}
                title={asset.data.alt ? undefined : "Add alt text in the Media library before using this image"}
                className="group relative aspect-square overflow-hidden rounded-md bg-muted disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Image
                  src={asset.data.thumbnailUrl ?? asset.data.url}
                  alt={asset.data.alt ?? ""}
                  fill
                  sizes="150px"
                  className="object-cover transition-transform group-hover:scale-[1.03]"
                />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function fieldLabel(key: string): string {
  const spaced = key.replace(/([A-Z])/g, " $1");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

function emptyToUndefined(value: string): string | undefined {
  return value === "" ? undefined : value;
}

/**
 * Collapsed by default when optional and unset, same as ObjectSection — and for the same
 * underlying reason, not just visual consistency: react-hook-form registers whatever
 * inputs actually mount, so an *always*-rendered url/alt pair would submit `{url: "",
 * alt: ""}` for a cover image nobody set, and Zod's `.url()` rejects that empty string
 * outright (it runs the format check before `.optional()` gets a say — an object with the
 * key present, even both fields empty, isn't the same as the key being absent). Collapsing
 * until there's an explicit "Add image" click means those inputs never register at all
 * until there's something to put in them.
 */
export function MediaField({ name, field }: { name: string; field: ResolvedField }) {
  const { register, watch, setValue } = useFormContext();
  const [libraryOpen, setLibraryOpen] = useState(false);
  const currentUrl = watch(`${name}.url`) as string | undefined;
  const [expanded, setExpanded] = useState(field.required || Boolean(currentUrl));
  const url: string | undefined = watch(`${name}.url`);
  const alt: string | undefined = watch(`${name}.alt`);

  function pick(asset: MediaAssetLike) {
    setValue(`${name}.url`, asset.url, { shouldDirty: true });
    setValue(`${name}.alt`, asset.alt ?? "", { shouldDirty: true });
    setLibraryOpen(false);
  }

  function clear() {
    setValue(name, undefined, { shouldDirty: true });
    setExpanded(false);
  }

  if (!expanded) {
    return (
      <button
        type="button"
        onClick={() => setExpanded(true)}
        className="flex items-center gap-1.5 rounded-md border border-dashed border-border px-3 py-2 text-sm text-muted-foreground hover:border-accent hover:text-accent"
      >
        <Plus className="h-3.5 w-3.5" aria-hidden="true" />
        Add {fieldLabel(field.key)}
      </button>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">
          {fieldLabel(field.key)}
          {field.required ? <span className="text-accent"> *</span> : null}
        </span>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setLibraryOpen(true)}
            className="text-xs text-accent hover:underline"
          >
            Browse library
          </button>
          {!field.required ? (
            <button type="button" onClick={clear} className="text-xs text-muted-foreground hover:text-foreground">
              Remove
            </button>
          ) : null}
        </div>
      </div>

      <div className="flex gap-4">
        <div className="relative flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-md border border-border bg-muted">
          {url ? (
            <Image src={url} alt={alt ?? ""} fill sizes="96px" className="object-cover" />
          ) : (
            <ImageOff className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
          )}
        </div>
        <div className="flex flex-1 flex-col gap-2">
          <input
            type="url"
            placeholder="Image URL"
            className={inputClass}
            {...register(`${name}.url`, { setValueAs: emptyToUndefined })}
          />
          <input
            type="text"
            placeholder="Alt text (required before this image can be used)"
            className={cn(inputClass, !alt && url ? "border-red-500/60" : "")}
            {...register(`${name}.alt`, { setValueAs: emptyToUndefined })}
          />
        </div>
      </div>

      {libraryOpen ? <LibraryDialog onPick={pick} onClose={() => setLibraryOpen(false)} /> : null}
    </div>
  );
}
