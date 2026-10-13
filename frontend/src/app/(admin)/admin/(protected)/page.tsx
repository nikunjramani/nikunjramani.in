"use client";

import {
  Award,
  Briefcase,
  FolderKanban,
  GraduationCap,
  Mail,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { listRecords } from "@/lib/api/content";
import { listMessages } from "@/lib/api/messages";
import { listAuditLog, type AuditEntry } from "@/lib/api/system";
import { ADMIN_SCHEMAS } from "@/generated/admin-schemas";
import { timeAgo } from "@/lib/format";

const COUNTED = [
  { key: "Project", label: "Projects", icon: FolderKanban },
  { key: "Skill", label: "Skills", icon: Sparkles },
  { key: "Experience", label: "Experience", icon: Briefcase },
  { key: "Education", label: "Education", icon: GraduationCap },
  { key: "Certification", label: "Certifications", icon: Award },
] as const;

export default function AdminDashboardPage() {
  const [counts, setCounts] = useState<Record<string, number> | null>(null);
  const [unread, setUnread] = useState<number | null>(null);
  const [recent, setRecent] = useState<AuditEntry[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [countPairs, messages, auditLog] = await Promise.all([
          Promise.all(
            COUNTED.map(async ({ key }) => {
              const domain = ADMIN_SCHEMAS[key as keyof typeof ADMIN_SCHEMAS].apiDomain;
              const records = await listRecords(domain);
              return [key, records.length] as const;
            }),
          ),
          listMessages(true),
          listAuditLog({ limit: 8 }),
        ]);
        if (cancelled) return;
        setCounts(Object.fromEntries(countPairs));
        setUnread(messages.length);
        setRecent(auditLog);
      } catch {
        if (!cancelled) setError(true);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>

      {error ? (
        <p className="text-sm text-red-500">Couldn&apos;t load dashboard data — try refreshing.</p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            {COUNTED.map(({ key, label, icon: Icon }) => (
              <Link
                key={key}
                href={`/admin/${ADMIN_SCHEMAS[key as keyof typeof ADMIN_SCHEMAS].apiDomain}`}
                className="rounded-lg border border-border bg-surface p-4 transition-colors hover:border-accent"
              >
                <Icon className="mb-2 h-4 w-4 text-muted-foreground" aria-hidden="true" />
                <p className="text-2xl font-semibold tabular-nums">{counts?.[key] ?? "–"}</p>
                <p className="text-xs text-muted-foreground">{label}</p>
              </Link>
            ))}
            <Link
              href="/admin/messages"
              className="rounded-lg border border-border bg-surface p-4 transition-colors hover:border-accent"
            >
              <Mail className="mb-2 h-4 w-4 text-muted-foreground" aria-hidden="true" />
              <p className="text-2xl font-semibold tabular-nums">{unread ?? "–"}</p>
              <p className="text-xs text-muted-foreground">Unread messages</p>
            </Link>
          </div>

          <section>
            <h2 className="mb-3 text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Recent activity
            </h2>
            {recent === null ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : recent.length === 0 ? (
              <p className="text-sm text-muted-foreground">Nothing yet.</p>
            ) : (
              <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
                {recent.map((entry) => (
                  <li key={entry.id} className="flex items-center justify-between gap-4 px-4 py-2.5 text-sm">
                    <span>
                      <span className="font-medium">{entry.actorEmail ?? entry.actor}</span>{" "}
                      <span className="text-muted-foreground">
                        {entry.action}d {entry.collection}
                        {entry.docId ? `/${entry.docId}` : ""}
                      </span>
                    </span>
                    <span className="shrink-0 text-xs text-muted-foreground">{timeAgo(entry.at)}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
