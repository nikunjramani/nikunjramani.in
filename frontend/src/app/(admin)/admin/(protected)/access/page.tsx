"use client";

import { Loader2, ShieldCheck, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { useFeedback } from "@/admin/components/ui-feedback";
import { ApiError } from "@/admin/api/client";
import { grantAdmin, listAdmins, revokeAdmin, type Admin } from "@/admin/api/identity";

export default function AdminAccessPage() {
  const [admins, setAdmins] = useState<Admin[] | null>(null);
  const [error, setError] = useState(false);
  const [email, setEmail] = useState("");
  const [granting, setGranting] = useState(false);
  const { toast, confirm } = useFeedback();

  const load = useCallback(() => {
    listAdmins()
      .then(setAdmins)
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleGrant(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    setGranting(true);
    try {
      await grantAdmin(email.trim());
      toast(`${email.trim()} is now an admin — from their next sign-in.`);
      setEmail("");
      load();
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Couldn't grant access.", "error");
    } finally {
      setGranting(false);
    }
  }

  async function handleRevoke(admin: Admin) {
    const who = admin.email ?? admin.uid;
    if (!(await confirm(`Remove admin access for ${who}? They'll be signed out everywhere.`))) return;
    try {
      await revokeAdmin(admin.uid);
      toast(`${who} is no longer an admin.`);
      load();
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Couldn't remove access.", "error");
    }
  }

  return (
    <div className="flex max-w-2xl flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Access</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Who can sign in to this panel. Sign-in is Google; admin access is the <code>admin</code>{" "}
          claim on the account.
        </p>
      </div>

      <form onSubmit={handleGrant} className="flex gap-2">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email of someone who has signed in once"
          className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={granting || !email.trim()}
          className="inline-flex items-center gap-1.5 rounded-md bg-accent px-3 py-2 text-sm text-accent-foreground hover:opacity-90 disabled:opacity-50"
        >
          {granting ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
          Grant
        </button>
      </form>

      {error ? (
        <p className="text-sm text-red-500">Couldn&apos;t load admins — try refreshing.</p>
      ) : admins === null ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <ul className="flex flex-col divide-y divide-border rounded-lg border border-border">
          {admins.map((admin) => (
            <li key={admin.uid} className="flex items-center justify-between gap-4 px-4 py-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{admin.email ?? admin.uid}</p>
                {admin.displayName ? (
                  <p className="truncate text-xs text-muted-foreground">{admin.displayName}</p>
                ) : null}
              </div>
              <button
                type="button"
                onClick={() => handleRevoke(admin)}
                aria-label={`Remove admin access for ${admin.email ?? admin.uid}`}
                className="rounded p-1.5 text-muted-foreground hover:text-red-500"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
