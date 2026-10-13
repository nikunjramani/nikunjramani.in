"use client";

import { ChevronDown, ChevronUp, Copy, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { useFeedback } from "@/components/admin/ui-feedback";
import { useRecordList } from "@/components/admin/use-record-list";
import { ADMIN_SCHEMAS } from "@/generated/admin-schemas";
import type { Project } from "@/generated/types";
import { ApiError } from "@/lib/api/client";
import type { RecordOut } from "@/lib/api/content";
import { duplicateProject } from "@/lib/api/projects";

const entry = ADMIN_SCHEMAS.Project;
const KIND_OPTIONS = (entry.properties.kind.enum ?? []) as string[];
const VISIBILITY_OPTIONS = (entry.properties.visibility.enum ?? []) as string[];

export default function AdminProjectsPage() {
  const { records, error, load, remove, move } = useRecordList<Project>(entry.apiDomain);
  const [search, setSearch] = useState("");
  const [kindFilter, setKindFilter] = useState("");
  const [visibilityFilter, setVisibilityFilter] = useState("");
  const { toast } = useFeedback();

  const filtered = useMemo(() => {
    if (!records) return [];
    return records.filter((r) => {
      if (kindFilter && r.data.kind !== kindFilter) return false;
      if (visibilityFilter && r.data.visibility !== visibilityFilter) return false;
      if (search) {
        const needle = search.toLowerCase();
        if (!r.data.title.toLowerCase().includes(needle) && !r.data.slug.toLowerCase().includes(needle)) {
          return false;
        }
      }
      return true;
    });
  }, [records, search, kindFilter, visibilityFilter]);

  const filtersActive = Boolean(search || kindFilter || visibilityFilter);

  async function handleDuplicate(record: RecordOut<Project>) {
    try {
      await duplicateProject(record.id);
      toast("Project duplicated.");
      load();
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Duplicate failed.", "error");
    }
  }

  function moveProject(index: number, direction: -1 | 1) {
    // Reordering a filtered view would scramble the real order, so it's whole-list only.
    if (!records || filtersActive) return;
    void move(records, index, direction);
  }

  if (error) {
    return <p className="text-sm text-red-500">Couldn&apos;t load projects — try refreshing.</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">Projects</h1>
        <Link
          href="/admin/projects/new"
          className="inline-flex items-center gap-1.5 rounded-md bg-accent px-3 py-1.5 text-sm text-accent-foreground hover:opacity-90"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          New
        </Link>
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Search title or slug…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="min-w-48 rounded-md border border-border bg-background px-3 py-1.5 text-sm"
        />
        <select
          value={kindFilter}
          onChange={(e) => setKindFilter(e.target.value)}
          className="rounded-md border border-border bg-background px-3 py-1.5 text-sm"
        >
          <option value="">All kinds</option>
          {KIND_OPTIONS.map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
        <select
          value={visibilityFilter}
          onChange={(e) => setVisibilityFilter(e.target.value)}
          className="rounded-md border border-border bg-background px-3 py-1.5 text-sm"
        >
          <option value="">All visibility</option>
          {VISIBILITY_OPTIONS.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
      </div>

      {records === null ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : filtered.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          {records.length === 0 ? "No projects yet." : "No projects match these filters."}
        </p>
      ) : (
        <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
          {filtered.map((record) => {
            const index = records.findIndex((r) => r.id === record.id);
            return (
              <li key={record.id} className="flex items-center justify-between gap-4 px-4 py-3">
                <Link href={`/admin/projects/${record.id}`} className="flex-1">
                  <p className="text-sm font-medium">{record.data.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {record.data.kind} · {record.data.status} · {record.data.visibility}
                  </p>
                </Link>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => moveProject(index, -1)}
                    disabled={filtersActive || index === 0}
                    aria-label="Move up"
                    className="rounded p-1.5 text-muted-foreground hover:text-foreground disabled:opacity-30"
                  >
                    <ChevronUp className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => moveProject(index, 1)}
                    disabled={filtersActive || index === records.length - 1}
                    aria-label="Move down"
                    className="rounded p-1.5 text-muted-foreground hover:text-foreground disabled:opacity-30"
                  >
                    <ChevronDown className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDuplicate(record)}
                    aria-label="Duplicate"
                    className="rounded p-1.5 text-muted-foreground hover:text-foreground"
                  >
                    <Copy className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => remove(record, record.data.title)}
                    aria-label="Delete"
                    className="rounded p-1.5 text-muted-foreground hover:text-red-500"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
