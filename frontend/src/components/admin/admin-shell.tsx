import type { ReactNode } from "react";

import { AdminNav } from "@/components/admin/admin-nav";
import { Breadcrumbs } from "@/components/admin/breadcrumbs";
import { UserMenu } from "@/components/admin/user-menu";

export function AdminShell({ email, children }: { email: string | undefined; children: ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-56 shrink-0 border-r border-border sm:block">
        <div className="border-b border-border px-4 py-4 text-sm font-medium">Admin</div>
        <AdminNav />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border px-6 py-3">
          <Breadcrumbs />
          <UserMenu email={email} />
        </header>

        <main className="flex-1 px-6 py-6">{children}</main>
      </div>
    </div>
  );
}
