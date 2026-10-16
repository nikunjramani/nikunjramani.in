"use client";

import { AlertTriangle, Download } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { downloadMessagesCsv, listMessages, type MessageRecordOut } from "@/admin/api/messages";
import { timeAgo } from "@/admin/lib/format";
import { cn } from "@/lib/utils";

export default function AdminMessagesPage() {
  const [messages, setMessages] = useState<MessageRecordOut[] | null>(null);
  const [error, setError] = useState(false);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    listMessages(unreadOnly)
      .then(setMessages)
      .catch(() => setError(true));
  }, [unreadOnly]);

  async function handleExport() {
    setExporting(true);
    try {
      await downloadMessagesCsv();
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">Messages</h1>
        <button
          type="button"
          onClick={handleExport}
          disabled={exporting}
          className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm hover:bg-muted disabled:opacity-50"
        >
          <Download className="h-4 w-4" aria-hidden="true" />
          Export CSV
        </button>
      </div>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setUnreadOnly(false)}
          className={cn(
            "rounded-full border px-3 py-1 text-sm",
            !unreadOnly ? "border-accent text-accent" : "border-border text-muted-foreground",
          )}
        >
          All
        </button>
        <button
          type="button"
          onClick={() => setUnreadOnly(true)}
          className={cn(
            "rounded-full border px-3 py-1 text-sm",
            unreadOnly ? "border-accent text-accent" : "border-border text-muted-foreground",
          )}
        >
          Unread
        </button>
      </div>

      {error ? (
        <p className="text-sm text-red-500">Couldn&apos;t load messages — try refreshing.</p>
      ) : messages === null ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : messages.length === 0 ? (
        <p className="text-sm text-muted-foreground">{unreadOnly ? "No unread messages." : "No messages yet."}</p>
      ) : (
        <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
          {messages.map((m) => (
            <li key={m.id}>
              <Link
                href={`/admin/messages/${m.id}`}
                className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-muted"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    {!m.data.read ? <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent" /> : null}
                    <p className={cn("truncate text-sm", !m.data.read ? "font-semibold" : "font-normal")}>
                      {m.data.name}
                    </p>
                    <span className="shrink-0 text-xs text-muted-foreground">{m.data.email}</span>
                    {m.data.spamScore && m.data.spamScore > 0.5 ? (
                      <span
                        title={`Spam score: ${m.data.spamScore.toFixed(2)}`}
                        className="inline-flex shrink-0 items-center gap-0.5 rounded-full bg-amber-500/10 px-1.5 py-0.5 text-xs text-amber-500"
                      >
                        <AlertTriangle className="h-3 w-3" /> Possible spam
                      </span>
                    ) : null}
                    {m.data.replied ? (
                      <span className="shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                        Replied
                      </span>
                    ) : null}
                  </div>
                  <p className="truncate text-sm text-muted-foreground">
                    {m.data.subject ? `${m.data.subject} — ` : ""}
                    {m.data.message}
                  </p>
                </div>
                <span className="shrink-0 text-xs text-muted-foreground">{timeAgo(m.data.createdAt)}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
