"use client";

import { useEffect, useState } from "react";
import type { z } from "zod";

import { SchemaForm } from "@/components/admin/schema-form/schema-form";
import { useFeedback } from "@/components/admin/ui-feedback";
import type { AdminSchemaEntry } from "@/generated/admin-schemas";
import { ApiError } from "@/lib/api/client";
import { getSingleton, patchSingleton, putSingleton } from "@/lib/api/content";

/** profile and site-config: one fixed document, no list/create/delete/reorder — just the
 * form, loaded and saved directly against shared/crud.py's singleton_id="main" routes.
 *
 * A singleton document isn't guaranteed to exist — nothing creates site_config/main
 * automatically, so a fresh environment 404s on the first load. That's not a load
 * failure to show an error for; it's the normal state before anyone has saved settings
 * once. GET 404 is treated as "no data yet" (empty defaults, first save creates it via
 * PUT rather than PATCH, since PATCH's merge-patch has nothing to patch against a
 * document that doesn't exist). */
export function SingletonScreen<T extends z.ZodTypeAny>({
  entry,
  zodSchema,
  title,
}: {
  entry: AdminSchemaEntry;
  zodSchema: T;
  title: string;
}) {
  type Data = Record<string, unknown>;
  const [data, setData] = useState<Data | null>(null);
  const [exists, setExists] = useState(false);
  const [error, setError] = useState(false);
  const { toast } = useFeedback();

  useEffect(() => {
    getSingleton<Data>(entry.apiDomain)
      .then((r) => {
        setData(r.data);
        setExists(true);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) {
          setData({});
          setExists(false);
          return;
        }
        setError(true);
      });
  }, [entry.apiDomain]);

  async function handleSubmit(values: z.infer<T>) {
    if (exists) {
      await patchSingleton(entry.apiDomain, values as Record<string, unknown>);
    } else {
      await putSingleton(entry.apiDomain, values);
      setExists(true);
    }
    toast(`${title} saved.`);
  }

  return (
    <div className="flex max-w-2xl flex-col gap-6">
      <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
      {error ? (
        <p className="text-sm text-red-500">Couldn&apos;t load {title.toLowerCase()} — try refreshing.</p>
      ) : data === null ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <>
          {!exists ? (
            <p className="text-sm text-muted-foreground">
              Nothing saved yet — fill in the fields below and save to create it.
            </p>
          ) : null}
          <SchemaForm
            entry={entry}
            zodSchema={zodSchema}
            defaultValues={data as z.infer<T>}
            onSubmit={handleSubmit}
          />
        </>
      )}
    </div>
  );
}
