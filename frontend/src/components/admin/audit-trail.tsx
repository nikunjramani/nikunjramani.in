"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api/client";

interface AuditEntry {
  id: string;
  actor: string;
  actorEmail?: string;
  action: string;
  collection: string;
  docId?: string;
  at: string;
}

/** Per-document history — GET /system/audit-log, filtered to this one record. Every admin
 * mutation already writes one of these (shared/services/audit.py); this is just the first
 * thing that ever reads them back. */
export function AuditTrail({ collection, docId }: { collection: string; docId: string }) {
  const [entries, setEntries] = useState<AuditEntry[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    apiFetch<AuditEntry[]>(
      `/system/audit-log?collection=${encodeURIComponent(collection)}&docId=${encodeURIComponent(docId)}&limit=20`,
    )
      .then(setEntries)
      .catch(() => setError(true));
  }, [collection, docId]);

  if (error || (entries && entries.length === 0)) return null;

  return (
    <details className="rounded-lg border border-border">
      <summary className="cursor-pointer px-4 py-2.5 text-xs font-medium text-muted-foreground uppercase tracking-wide">
        History
      </summary>
      <ul className="flex flex-col divide-y divide-border border-t border-border">
        {entries === null ? (
          <li className="px-4 py-2.5 text-sm text-muted-foreground">Loading…</li>
        ) : (
          entries.map((entry) => (
            <li key={entry.id} className="flex items-center justify-between gap-4 px-4 py-2 text-sm">
              <span>
                <span className="font-medium">{entry.actorEmail ?? entry.actor}</span>{" "}
                <span className="text-muted-foreground">{entry.action}d</span>
              </span>
              <span className="shrink-0 text-xs text-muted-foreground">
                {new Date(entry.at).toLocaleString()}
              </span>
            </li>
          ))
        )}
      </ul>
    </details>
  );
}
