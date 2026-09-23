import type { Metadata } from "next";

import { SignInPanel } from "@/components/admin/sign-in-panel";

export const metadata: Metadata = {
  title: "Admin sign in",
  robots: { index: false, follow: false },
};

export default function AdminLoginPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 px-6">
      <div className="text-center">
        <h1 className="text-xl font-semibold tracking-tight">nikunjramani.in admin</h1>
        <p className="mt-1 text-sm text-muted-foreground">Sign in with your Google account.</p>
      </div>
      <SignInPanel />
    </div>
  );
}
