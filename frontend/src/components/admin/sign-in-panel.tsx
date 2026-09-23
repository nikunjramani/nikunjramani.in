"use client";

import { GoogleAuthProvider, signInWithPopup, signOut } from "firebase/auth";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { GoogleIcon } from "@/components/admin/google-icon";
import { auth } from "@/lib/firebase/client";

type Status = "idle" | "signing-in" | "not-admin" | "error";

export function SignInPanel() {
  const [status, setStatus] = useState<Status>("idle");
  const router = useRouter();

  async function signIn() {
    setStatus("signing-in");
    try {
      const credential = await signInWithPopup(auth(), new GoogleAuthProvider());
      const idToken = await credential.user.getIdToken();

      const res = await fetch("/api/admin/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idToken }),
      });
      if (!res.ok) throw new Error(`session exchange failed: ${res.status}`);

      const claims = await credential.user.getIdTokenResult();
      if (claims.claims.admin !== true) {
        // A valid Google sign-in that isn't an authorised admin is not an error — it's an
        // expected outcome that needs a clear message, not a silent redirect loop back to
        // this same page (which is what happens if this case isn't handled explicitly: no
        // session cookie ever gets cleared, so the client keeps thinking it's signed in).
        await fetch("/api/admin/session", { method: "DELETE" });
        await signOut(auth());
        setStatus("not-admin");
        return;
      }

      router.push("/admin");
      router.refresh();
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  }

  if (status === "not-admin") {
    return (
      <div className="flex flex-col items-center gap-3 text-center">
        <p className="font-medium">Signed in, but this account isn&apos;t an admin.</p>
        <p className="max-w-sm text-sm text-muted-foreground">
          Your Google account doesn&apos;t have admin access to this site. If you think this is a
          mistake, the admin claim needs to be granted from the command line — see{" "}
          <code className="rounded bg-muted px-1 py-0.5">infra/scripts/set_admin_claim.py</code>.
        </p>
        <button
          type="button"
          onClick={() => setStatus("idle")}
          className="mt-2 text-sm text-accent hover:underline"
        >
          Try a different account
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4">
      <button
        type="button"
        onClick={signIn}
        disabled={status === "signing-in"}
        className="inline-flex items-center gap-2.5 rounded-md border border-border bg-surface px-5 py-2.5 text-sm font-medium transition-colors hover:bg-muted disabled:opacity-60"
      >
        <GoogleIcon className="h-4 w-4" />
        {status === "signing-in" ? "Signing in…" : "Sign in with Google"}
      </button>
      {status === "error" ? (
        <p className="text-sm text-red-500">Sign-in failed — please try again.</p>
      ) : null}
    </div>
  );
}
