"use client";

import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

interface Toast {
  id: number;
  message: string;
  kind: "success" | "error";
}

interface ConfirmRequest {
  message: string;
  resolve: (ok: boolean) => void;
}

interface FeedbackContextValue {
  toast: (message: string, kind?: Toast["kind"]) => void;
  confirm: (message: string) => Promise<boolean>;
}

const FeedbackContext = createContext<FeedbackContextValue | null>(null);

export function useFeedback(): FeedbackContextValue {
  const ctx = useContext(FeedbackContext);
  if (!ctx) throw new Error("useFeedback must be used within FeedbackProvider");
  return ctx;
}

let nextId = 0;

/** One provider for both toasts and confirm dialogs — every content screen needs both
 * (optimistic-update feedback, delete confirmation), and they're the same class of
 * "transient UI outside the normal component tree" problem. */
export function FeedbackProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [confirmRequest, setConfirmRequest] = useState<ConfirmRequest | null>(null);

  const toast = useCallback((message: string, kind: Toast["kind"] = "success") => {
    const id = nextId++;
    setToasts((t) => [...t, { id, message, kind }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
  }, []);

  const confirm = useCallback((message: string) => {
    return new Promise<boolean>((resolve) => {
      setConfirmRequest({ message, resolve });
    });
  }, []);

  return (
    <FeedbackContext.Provider value={{ toast, confirm }}>
      {children}

      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className="flex items-center gap-2 rounded-md border border-border bg-surface px-4 py-2.5 text-sm shadow-lg"
          >
            {t.kind === "success" ? (
              <CheckCircle2 className="h-4 w-4 text-accent" aria-hidden="true" />
            ) : (
              <XCircle className="h-4 w-4 text-red-500" aria-hidden="true" />
            )}
            {t.message}
          </div>
        ))}
      </div>

      {confirmRequest ? (
        <div
          role="alertdialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-6"
          onClick={() => {
            confirmRequest.resolve(false);
            setConfirmRequest(null);
          }}
        >
          <div
            className="flex w-full max-w-sm flex-col gap-4 rounded-lg border border-border bg-background p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 shrink-0 text-red-500" aria-hidden="true" />
              <p className="text-sm">{confirmRequest.message}</p>
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  confirmRequest.resolve(false);
                  setConfirmRequest(null);
                }}
                className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-muted"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  confirmRequest.resolve(true);
                  setConfirmRequest(null);
                }}
                className="rounded-md bg-red-500 px-3 py-1.5 text-sm text-white hover:opacity-90"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </FeedbackContext.Provider>
  );
}
