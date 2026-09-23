import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { AdminShell } from "@/components/admin/admin-shell";
import { getAdminSession, isAdmin } from "@/lib/auth/session";

export default async function ProtectedAdminLayout({ children }: { children: ReactNode }) {
  const claims = await getAdminSession();

  // No valid session at all: middleware normally catches this first, but a cookie can
  // expire between requests, and middleware only checks presence, not validity — this is
  // the actual re-check. Redirecting (not erroring) because an expired session is routine,
  // not exceptional.
  if (!claims) redirect("/admin/login");

  // A *valid* session that just isn't an admin is different: redirecting back to login
  // would bounce the visitor in a loop (they can sign in fine, they're just not
  // authorised), so this shows an explicit refusal instead — see 5.1's own requirement.
  if (!isAdmin(claims)) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-6 text-center">
        <p className="font-medium">Signed in, but this account isn&apos;t an admin.</p>
        <p className="max-w-sm text-sm text-muted-foreground">
          {claims.email} doesn&apos;t have admin access. Grant it with{" "}
          <code className="rounded bg-muted px-1 py-0.5">infra/scripts/set_admin_claim.py</code>,
          then sign out and back in.
        </p>
        <a href="/admin/login" className="mt-2 text-sm text-accent hover:underline">
          Back to sign in
        </a>
      </div>
    );
  }

  return <AdminShell email={claims.email}>{children}</AdminShell>;
}
