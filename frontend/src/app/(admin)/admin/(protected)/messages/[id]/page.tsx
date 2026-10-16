"use client";

import { AlertTriangle, ArrowLeft, Check, Mail, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useFeedback } from "@/admin/components/ui-feedback";
import { ApiError } from "@/admin/api/client";
import {
  deleteMessage,
  getMessage,
  markMessageRead,
  markMessageReplied,
  type MessageRecordOut,
} from "@/admin/api/messages";

export default function AdminMessageDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { toast, confirm } = useFeedback();
  const [record, setRecord] = useState<MessageRecordOut | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getMessage(params.id)
      .then(async (r) => {
        setRecord(r);
        // Opening the detail view is the read action — matches every other inbox's UX,
        // and avoids a separate "mark as read" click for the common case.
        if (!r.data.read) {
          const updated = await markMessageRead(params.id);
          setRecord(updated);
        }
      })
      .catch(() => setError(true));
  }, [params.id]);

  async function handleMarkReplied() {
    if (!record) return;
    try {
      const updated = await markMessageReplied(record.id);
      setRecord(updated);
      toast("Marked as replied.");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Couldn't update.", "error");
    }
  }

  async function handleDelete() {
    if (!record) return;
    const ok = await confirm(`Delete this message from ${record.data.name}? This can't be undone.`);
    if (!ok) return;
    try {
      await deleteMessage(record.id);
      toast("Message deleted.");
      router.push("/admin/messages");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Delete failed.", "error");
    }
  }

  if (error) {
    return <p className="text-sm text-red-500">Couldn&apos;t load this message — try refreshing.</p>;
  }
  if (!record) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  const { data } = record;
  const mailtoHref = `mailto:${data.email}?subject=${encodeURIComponent(
    `Re: ${data.subject || "Your message"}`,
  )}`;

  return (
    <div className="flex max-w-2xl flex-col gap-6">
      <Link href="/admin/messages" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> All messages
      </Link>

      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">{data.subject || "No subject"}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {data.name} &lt;{data.email}&gt;
          </p>
          {data.createdAt ? (
            <p className="text-xs text-muted-foreground">{new Date(data.createdAt).toLocaleString()}</p>
          ) : null}
        </div>
        {data.spamScore && data.spamScore > 0.5 ? (
          <span
            title={`Spam score: ${data.spamScore.toFixed(2)}`}
            className="inline-flex shrink-0 items-center gap-1 rounded-full bg-amber-500/10 px-2 py-1 text-xs text-amber-500"
          >
            <AlertTriangle className="h-3.5 w-3.5" /> Possible spam
          </span>
        ) : null}
      </div>

      <p className="whitespace-pre-wrap rounded-lg border border-border bg-surface p-4 text-sm">{data.message}</p>

      <div className="flex items-center gap-3 border-t border-border pt-4">
        <a
          href={mailtoHref}
          className="inline-flex items-center gap-1.5 rounded-md bg-accent px-4 py-2 text-sm text-accent-foreground hover:opacity-90"
        >
          <Mail className="h-4 w-4" /> Reply
        </a>
        {!data.replied ? (
          <button
            type="button"
            onClick={handleMarkReplied}
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-4 py-2 text-sm hover:bg-muted"
          >
            <Check className="h-4 w-4" /> Mark replied
          </button>
        ) : (
          <span className="inline-flex items-center gap-1.5 text-sm text-muted-foreground">
            <Check className="h-4 w-4" /> Replied
          </span>
        )}
        <button
          type="button"
          onClick={handleDelete}
          className="ml-auto inline-flex items-center gap-1.5 rounded-md p-2 text-muted-foreground hover:text-red-500"
          aria-label="Delete message"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
