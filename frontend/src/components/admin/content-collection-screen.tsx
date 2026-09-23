"use client";

import { ChevronDown, ChevronUp, Pencil, Plus, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import type { z } from "zod";

import { RecordFormDialog } from "@/components/admin/record-form-dialog";
import { useFeedback } from "@/components/admin/ui-feedback";
import type { AdminSchemaEntry } from "@/generated/admin-schemas";
import {
  createRecord,
  deleteRecord,
  listRecords,
  patchRecord,
  reorderRecords,
  type RecordOut,
} from "@/lib/api/content";
import { ApiError } from "@/lib/api/client";

const TITLE_KEYS = ["title", "name", "company", "institution"];
const SUBTITLE_KEYS = ["headline", "role", "qualification", "issuer", "summary"];

function pick(data: Record<string, unknown>, keys: string[]): string | undefined {
  for (const key of keys) {
    const value = data[key];
    if (typeof value === "string" && value) return value;
  }
  return undefined;
}

export function ContentCollectionScreen<T extends z.ZodTypeAny>({
  entry,
  zodSchema,
  title,
  groupBy,
}: {
  entry: AdminSchemaEntry;
  zodSchema: T;
  title: string;
  /** Optional field to group rows under a heading (e.g. Skill's "category"). */
  groupBy?: string;
}) {
  type Data = Record<string, unknown>;
  const [records, setRecords] = useState<RecordOut<Data>[] | null>(null);
  const [error, setError] = useState(false);
  const [dialog, setDialog] = useState<{ mode: "create" } | { mode: "edit"; record: RecordOut<Data> } | null>(
    null,
  );
  const { toast, confirm } = useFeedback();

  const load = useCallback(() => {
    listRecords<Data>(entry.apiDomain)
      .then(setRecords)
      .catch(() => setError(true));
  }, [entry.apiDomain]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate(values: z.infer<T>) {
    await createRecord(entry.apiDomain, values);
    toast(`${title} created.`);
    setDialog(null);
    load();
  }

  async function handleEdit(id: string, values: z.infer<T>) {
    await patchRecord(entry.apiDomain, id, values as Record<string, unknown>);
    toast(`${title} updated.`);
    setDialog(null);
    load();
  }

  async function handleDelete(record: RecordOut<Data>) {
    const name = pick(record.data, TITLE_KEYS) ?? record.id;
    const ok = await confirm(`Delete "${name}"? This can't be undone.`);
    if (!ok) return;
    const previous = records;
    setRecords((r) => r?.filter((x) => x.id !== record.id) ?? null);
    try {
      await deleteRecord(entry.apiDomain, record.id);
      toast(`${title} deleted.`);
    } catch (err) {
      setRecords(previous ?? null); // rollback — an optimistic delete that silently "worked" would look like a bug
      toast(err instanceof ApiError ? err.message : "Delete failed.", "error");
    }
  }

  async function move(index: number, direction: -1 | 1, group: RecordOut<Data>[]) {
    const target = index + direction;
    if (target < 0 || target >= group.length) return;
    const reordered = [...group];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    const ids = reordered.map((r) => r.id);
    const previous = records;
    setRecords((all) => (all ? mergeOrdered(all, reordered) : all));
    try {
      await reorderRecords(entry.apiDomain, ids);
    } catch (err) {
      setRecords(previous ?? null);
      toast(err instanceof ApiError ? err.message : "Reorder failed.", "error");
    }
  }

  function mergeOrdered(all: RecordOut<Data>[], reorderedGroup: RecordOut<Data>[]): RecordOut<Data>[] {
    const byId = new Map(reorderedGroup.map((r) => [r.id, r]));
    let cursor = 0;
    return all.map((r) => (byId.has(r.id) ? reorderedGroup[cursor++] : r));
  }

  if (error) {
    return <p className="text-sm text-red-500">Couldn&apos;t load {title.toLowerCase()}s — try refreshing.</p>;
  }

  const groups = groupRecords(records, groupBy);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        <button
          type="button"
          onClick={() => setDialog({ mode: "create" })}
          className="inline-flex items-center gap-1.5 rounded-md bg-accent px-3 py-1.5 text-sm text-accent-foreground hover:opacity-90"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          New
        </button>
      </div>

      {records === null ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : records.length === 0 ? (
        <p className="text-sm text-muted-foreground">Nothing yet.</p>
      ) : (
        <div className="flex flex-col gap-6">
          {groups.map(([groupName, group]) => (
            <div key={groupName ?? "_all"}>
              {groupName ? (
                <h2 className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  {groupName}
                </h2>
              ) : null}
              <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
                {group.map((record, index) => (
                  <li key={record.id} className="flex items-center justify-between gap-4 px-4 py-3">
                    <button
                      type="button"
                      onClick={() => setDialog({ mode: "edit", record })}
                      className="flex-1 text-left"
                    >
                      <p className="text-sm font-medium">{pick(record.data, TITLE_KEYS) ?? record.id}</p>
                      {pick(record.data, SUBTITLE_KEYS) ? (
                        <p className="text-xs text-muted-foreground">{pick(record.data, SUBTITLE_KEYS)}</p>
                      ) : null}
                    </button>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => move(index, -1, group)}
                        disabled={index === 0}
                        aria-label="Move up"
                        className="rounded p-1.5 text-muted-foreground hover:text-foreground disabled:opacity-30"
                      >
                        <ChevronUp className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => move(index, 1, group)}
                        disabled={index === group.length - 1}
                        aria-label="Move down"
                        className="rounded p-1.5 text-muted-foreground hover:text-foreground disabled:opacity-30"
                      >
                        <ChevronDown className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setDialog({ mode: "edit", record })}
                        aria-label="Edit"
                        className="rounded p-1.5 text-muted-foreground hover:text-foreground"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(record)}
                        aria-label="Delete"
                        className="rounded p-1.5 text-muted-foreground hover:text-red-500"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {dialog?.mode === "create" ? (
        <RecordFormDialog
          title={`New ${title.toLowerCase()}`}
          entry={entry}
          zodSchema={zodSchema}
          defaultValues={{} as z.infer<T>}
          onSubmit={handleCreate}
          onClose={() => setDialog(null)}
          submitLabel="Create"
        />
      ) : null}
      {dialog?.mode === "edit" ? (
        <RecordFormDialog
          title={`Edit ${title.toLowerCase()}`}
          entry={entry}
          zodSchema={zodSchema}
          defaultValues={dialog.record.data as z.infer<T>}
          onSubmit={(values) => handleEdit(dialog.record.id, values)}
          onClose={() => setDialog(null)}
        />
      ) : null}
    </div>
  );
}

function groupRecords<Data extends Record<string, unknown>>(
  records: RecordOut<Data>[] | null,
  groupBy: string | undefined,
): [string | null, RecordOut<Data>[]][] {
  if (!records) return [];
  if (!groupBy) return [[null, records]];

  const groups = new Map<string, RecordOut<Data>[]>();
  for (const record of records) {
    const key = typeof record.data[groupBy] === "string" ? (record.data[groupBy] as string) : "Other";
    groups.set(key, [...(groups.get(key) ?? []), record]);
  }
  return [...groups.entries()];
}
