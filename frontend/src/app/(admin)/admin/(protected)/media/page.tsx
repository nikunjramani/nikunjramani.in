"use client";

import { useCallback, useEffect, useState } from "react";

import { MediaCard } from "@/admin/components/media/media-card";
import { UploadZone } from "@/admin/components/media/upload-zone";
import { listMedia, type MediaRecordOut } from "@/admin/api-client/media";

export default function AdminMediaPage() {
  const [assets, setAssets] = useState<MediaRecordOut[] | null>(null);
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    listMedia()
      .then(setAssets)
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold tracking-tight">Media</h1>

      <UploadZone onUploaded={load} />

      {error ? (
        <p className="text-sm text-red-500">Couldn&apos;t load the media library — try refreshing.</p>
      ) : assets === null ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : assets.length === 0 ? (
        <p className="text-sm text-muted-foreground">No images uploaded yet.</p>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {assets.map((record) => (
            <MediaCard
              key={record.id}
              record={record}
              onChange={(updated) =>
                setAssets((prev) => prev?.map((a) => (a.id === updated.id ? updated : a)) ?? null)
              }
              onDelete={() => setAssets((prev) => prev?.filter((a) => a.id !== record.id) ?? null)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
