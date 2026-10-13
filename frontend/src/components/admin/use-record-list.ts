"use client";

import { useCallback, useEffect, useState } from "react";

import { useFeedback } from "@/components/admin/ui-feedback";
import { ApiError } from "@/lib/api/client";
import { deleteRecord, listRecords, reorderRecords, type RecordOut } from "@/lib/api/content";

/**
 * A content collection as an admin list screen sees it: load, optimistic delete with
 * rollback, and reorder within a (possibly grouped or filtered) slice of the list.
 * Shared by the generic collection screen and the projects screen.
 */
export function useRecordList<T>(apiDomain: string) {
  const [records, setRecords] = useState<RecordOut<T>[] | null>(null);
  const [error, setError] = useState(false);
  const { toast, confirm } = useFeedback();

  const load = useCallback(() => {
    listRecords<T>(apiDomain)
      .then(setRecords)
      .catch(() => setError(true));
  }, [apiDomain]);

  useEffect(() => {
    load();
  }, [load]);

  async function remove(record: RecordOut<T>, label: string): Promise<void> {
    if (!(await confirm(`Delete "${label}"? This can't be undone.`))) return;
    const previous = records;
    setRecords((all) => all?.filter((r) => r.id !== record.id) ?? null);
    try {
      await deleteRecord(apiDomain, record.id);
      toast(`"${label}" deleted.`);
    } catch (err) {
      setRecords(previous); // an optimistic delete that silently "worked" would look like a bug
      toast(err instanceof ApiError ? err.message : "Delete failed.", "error");
    }
  }

  /** Swap `slice[index]` with its neighbour, keeping every record outside `slice` where it
   * was. The server gets the whole list's new order: it numbers whatever ids it receives
   * 0..n-1, so sending only a slice would collide with the orders outside it. */
  async function move(slice: RecordOut<T>[], index: number, direction: -1 | 1): Promise<void> {
    const target = index + direction;
    if (!records || target < 0 || target >= slice.length) return;
    const reordered = [...slice];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    const inSlice = new Set(reordered.map((r) => r.id));
    let cursor = 0;
    const next = records.map((r) => (inSlice.has(r.id) ? reordered[cursor++] : r));
    const previous = records;
    setRecords(next);
    try {
      await reorderRecords(apiDomain, next.map((r) => r.id));
    } catch (err) {
      setRecords(previous);
      toast(err instanceof ApiError ? err.message : "Reorder failed.", "error");
    }
  }

  return { records, error, load, remove, move };
}
