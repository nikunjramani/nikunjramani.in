"use client";

import { LogOut } from "lucide-react";
import { signOut } from "firebase/auth";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { auth } from "@/lib/firebase/client";

export function UserMenu({ email }: { email: string | undefined }) {
  const [signingOut, setSigningOut] = useState(false);
  const router = useRouter();

  async function handleSignOut() {
    setSigningOut(true);
    await fetch("/api/admin/session", { method: "DELETE" });
    await signOut(auth());
    router.push("/admin/login");
    router.refresh();
  }

  return (
    <div className="flex items-center gap-3">
      {email ? <span className="text-sm text-muted-foreground">{email}</span> : null}
      <button
        type="button"
        onClick={handleSignOut}
        disabled={signingOut}
        className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm transition-colors hover:bg-muted disabled:opacity-60"
      >
        <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
        {signingOut ? "Signing out…" : "Sign out"}
      </button>
    </div>
  );
}
