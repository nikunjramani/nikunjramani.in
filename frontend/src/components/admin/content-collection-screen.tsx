"use client";

import { ChevronDown, ChevronUp, Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import type { z } from "zod";

import { RecordFormDialog } from "@/components/admin/record-form-dialog";
import { useFeedback } from "@/components/admin/ui-feedback";
import { useRecordList } from "@/components/admin/use-record-list";
import type { AdminSchemaEntry } from "@/generated/admin-schemas";
import { createRecord, patchRecord, type RecordOut } from "@/lib/api/content";
import { toMergePatch } from "@/lib/merge-patch";

type Data = Record<string, unknown>;

const TITLE_KEYS = ["title", "name", "company", "institution"];
const SUBTITLE_KEYS = ["headline", "role", "qualification", "issuer", "summary"];

function pick(data: Data, keys: string[]): string | undefined {
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
  const { records, error, load, remove, move } = useRecordList<Data>(entry.apiDomain);
  const [dialog, setDialog] = useState<{ mode: "create" } | { mode: "edit"; record: RecordOut<Data> } | null>(
    null,
  );
  const { toast } = useFeedback();

  async function handleCreate(values: z.infer<T>) {
    await createRecord(entry.apiDomain, values);
    toast(`${title} created.`);
    setDialog(null);
    load();
  }

  async function handleEdit(record: RecordOut<Data>, values: z.infer<T>) {
    await patchRecord(entry.apiDomain, record.id, toMergePatch(record.data, values as Data));
    toast(`${title} updated.`);
    setDialog(null);
    load();
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
                        onClick={() => move(group, index, -1)}
                        disabled={index === 0}
                        aria-label="Move up"
                        className="rounded p-1.5 text-muted-foreground hover:text-foreground disabled:opacity-30"
                      >
                        <ChevronUp className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => move(group, index, 1)}
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
                        onClick={() => remove(record, pick(record.data, TITLE_KEYS) ?? record.id)}
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
          autosaveKey={`${entry.apiDomain}:new`}
        />
      ) : null}
      {dialog?.mode === "edit" ? (
        <RecordFormDialog
          title={`Edit ${title.toLowerCase()}`}
          entry={entry}
          zodSchema={zodSchema}
          defaultValues={dialog.record.data as z.infer<T>}
          onSubmit={(values) => handleEdit(dialog.record, values)}
          onClose={() => setDialog(null)}
          autosaveKey={`${entry.apiDomain}:${dialog.record.id}`}
          auditTrail={{ collection: entry.collection, docId: dialog.record.id }}
        />
      ) : null}
    </div>
  );
}

function groupRecords(
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
