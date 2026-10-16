"use client";

import { Loader2, UploadCloud, CheckCircle2, XCircle } from "lucide-react";
import { useCallback, useRef, useState } from "react";

import { requestUploadUrl, uploadToSignedUrl } from "@/admin/api-client/media";
import { cn } from "@/lib/utils";

const ACCEPTED_TYPES = ["image/webp", "image/jpeg", "image/png", "image/gif"];
const MAX_BYTES = 20 * 1024 * 1024;

interface UploadItem {
  id: string;
  name: string;
  status: "uploading" | "processing" | "done" | "error";
  error?: string;
}

/**
 * Drag-and-drop + multi-file, each going through the real two-step flow: a signed URL from
 * the Python API, then a direct PUT to Storage (not through Python — the whole point of a
 * signed URL is that it doesn't need to be). The resulting MediaAsset record doesn't exist
 * until on_media_uploaded finishes processing it, so "done" here means "uploaded", not
 * "ready" — onUploaded fires the parent's refresh poll rather than this component
 * pretending to know when the trigger has finished.
 */
export function UploadZone({ onUploaded }: { onUploaded: () => void }) {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | File[]) => {
      for (const file of Array.from(files)) {
        const id = `${file.name}-${Date.now()}-${Math.random()}`;

        if (!ACCEPTED_TYPES.includes(file.type)) {
          setItems((prev) => [
            ...prev,
            { id, name: file.name, status: "error", error: `Unsupported type: ${file.type}` },
          ]);
          continue;
        }
        if (file.size > MAX_BYTES) {
          setItems((prev) => [...prev, { id, name: file.name, status: "error", error: "File too large" }]);
          continue;
        }

        setItems((prev) => [...prev, { id, name: file.name, status: "uploading" }]);

        (async () => {
          try {
            const { uploadUrl } = await requestUploadUrl(file.type, file.size);
            await uploadToSignedUrl(uploadUrl, file);
            setItems((prev) => prev.map((i) => (i.id === id ? { ...i, status: "processing" } : i)));
            onUploaded();
            // Processing (WebP + thumbnail + blurhash) happens in the background trigger —
            // there's no webhook back to the browser, so this just gives it a few seconds
            // and lets the grid's own refresh pick up the finished record.
            setTimeout(() => {
              setItems((prev) => prev.map((i) => (i.id === id ? { ...i, status: "done" } : i)));
              onUploaded();
            }, 4000);
          } catch (err) {
            setItems((prev) =>
              prev.map((i) =>
                i.id === id
                  ? { ...i, status: "error", error: err instanceof Error ? err.message : "Upload failed" }
                  : i,
              ),
            );
          }
        })();
      }
    },
    [onUploaded],
  );

  return (
    <div className="flex flex-col gap-3">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        className={cn(
          "flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors cursor-pointer",
          dragOver ? "border-accent bg-accent/5" : "border-border hover:border-accent/50",
        )}
      >
        <UploadCloud className="h-6 w-6 text-muted-foreground" aria-hidden="true" />
        <p className="text-sm">Drag images here, or click to browse</p>
        <p className="text-xs text-muted-foreground">WebP, JPEG, PNG, GIF — up to 20MB each</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_TYPES.join(",")}
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.length) handleFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>

      {items.length ? (
        <ul className="flex flex-col gap-1.5">
          {items.map((item) => (
            <li key={item.id} className="flex items-center gap-2 text-sm">
              {item.status === "uploading" || item.status === "processing" ? (
                <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-muted-foreground" />
              ) : item.status === "done" ? (
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-accent" />
              ) : (
                <XCircle className="h-3.5 w-3.5 shrink-0 text-red-500" />
              )}
              <span className="truncate">{item.name}</span>
              <span className="shrink-0 text-xs text-muted-foreground">
                {item.status === "uploading" && "Uploading…"}
                {item.status === "processing" && "Processing…"}
                {item.status === "done" && "Done"}
                {item.status === "error" && (item.error ?? "Failed")}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
