"use client";

import { useEffect } from "react";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto flex max-w-4xl flex-col items-center justify-center gap-4 px-6 py-32 text-center">
      <p className="text-sm text-muted-foreground">Error</p>
      <h1 className="text-2xl font-medium tracking-tight">Something went wrong</h1>
      <button
        type="button"
        onClick={reset}
        className="mt-2 rounded-md bg-accent px-4 py-2 text-sm text-accent-foreground transition-opacity hover:opacity-90"
      >
        Try again
      </button>
    </div>
  );
}
