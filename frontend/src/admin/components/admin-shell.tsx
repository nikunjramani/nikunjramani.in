import type { ReactNode } from "react";

import { AdminNav } from "@/admin/components/admin-nav";
import { Breadcrumbs } from "@/admin/components/breadcrumbs";
import { FeedbackProvider } from "@/admin/components/ui-feedback";
import { UserMenu } from "@/admin/components/user-menu";

export function AdminShell({ email, children }: { email: string | undefined; children: ReactNode }) {
  return (
    <FeedbackProvider>
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

          <main id="main-content" className="flex-1 px-6 py-6">{children}</main>
        </div>
      </div>
    </FeedbackProvider>
  );
}
