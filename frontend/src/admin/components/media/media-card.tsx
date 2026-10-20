"use client";

import { AlertTriangle, Check, Copy, Loader2, Pencil, Trash2 } from "lucide-react";
import Image from "next/image";
import { useState } from "react";

import { useFeedback } from "@/admin/components/ui-feedback";
import { ApiError } from "@/admin/api-client/client";
import { deleteMedia, getMediaUsage, updateMediaMetadata, type MediaRecordOut } from "@/admin/api-client/media";
import { cn } from "@/lib/utils";

export function MediaCard({
  record,
  onChange,
  onDelete,
}: {
  record: MediaRecordOut;
  onChange: (updated: MediaRecordOut) => void;
  onDelete: () => void;
}) {
  const { toast, confirm } = useFeedback();
  const [editing, setEditing] = useState(false);
  const [alt, setAlt] = useState(record.data.alt ?? "");
  const [caption, setCaption] = useState(record.data.caption ?? "");
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);

  async function saveMetadata() {
    if (!alt.trim()) {
      toast("Alt text is required before this image can be used.", "error");
      return;
    }
    setSaving(true);
    try {
      const updated = await updateMediaMetadata(record.id, alt.trim(), caption.trim());
      onChange(updated);
      setEditing(false);
      toast("Alt text saved.");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Save failed.", "error");
    } finally {
      setSaving(false);
    }
  }

  async function copyUrl() {
    await navigator.clipboard.writeText(record.data.url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  async function handleDelete() {
    let references: string[];
    try {
      references = await getMediaUsage(record.id);
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Couldn't check where this image is used.", "error");
      return;
    }
    const message = references.length
      ? `This image is still used by ${references.join(", ")}. Deleting it will break ${
          references.length === 1 ? "that page" : "those pages"
        }. Delete anyway?`
      : "Delete this image? This can't be undone.";
    const ok = await confirm(message);
    if (!ok) return;
    try {
      await deleteMedia(record.id, { force: references.length > 0 });
      onDelete();
      toast("Image deleted.");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Delete failed.", "error");
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border bg-surface p-3">
      <div className="relative aspect-square overflow-hidden rounded-md bg-muted">
        <Image
          src={record.data.thumbnailUrl ?? record.data.url}
          alt={record.data.alt ?? ""}
          fill
          sizes="200px"
          className="object-cover"
        />
        {!record.data.alt ? (
          <span
            title="No alt text — can't be used yet"
            className="absolute top-1.5 right-1.5 rounded-full bg-background/90 p-1"
          >
            <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
          </span>
        ) : null}
      </div>

      {editing ? (
        <div className="flex flex-col gap-1.5">
          <input
            type="text"
            value={alt}
            onChange={(e) => setAlt(e.target.value)}
            placeholder="Alt text (required)"
            className="rounded border border-border bg-background px-2 py-1 text-xs"
            autoFocus
          />
          <input
            type="text"
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            placeholder="Caption (optional)"
            className="rounded border border-border bg-background px-2 py-1 text-xs"
          />
          <div className="flex gap-1.5">
            <button
              type="button"
              onClick={saveMetadata}
              disabled={saving}
              className="flex-1 rounded bg-accent px-2 py-1 text-xs text-accent-foreground hover:opacity-90 disabled:opacity-50"
            >
              {saving ? <Loader2 className="mx-auto h-3 w-3 animate-spin" /> : "Save"}
            </button>
            <button
              type="button"
              onClick={() => {
                setAlt(record.data.alt ?? "");
                setCaption(record.data.caption ?? "");
                setEditing(false);
              }}
              className="rounded border border-border px-2 py-1 text-xs hover:bg-muted"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <>
          <p className={cn("truncate text-xs", record.data.alt ? "text-foreground" : "text-amber-500")}>
            {record.data.alt || "No alt text"}
          </p>
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setEditing(true)}
              aria-label="Edit alt text"
              className="rounded p-1 text-muted-foreground hover:text-foreground"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>
            <button
              type="button"
              onClick={copyUrl}
              aria-label="Copy URL"
              className="rounded p-1 text-muted-foreground hover:text-foreground"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-accent" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
            <button
              type="button"
              onClick={handleDelete}
              aria-label="Delete"
              className="rounded p-1 text-muted-foreground hover:text-red-500"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
