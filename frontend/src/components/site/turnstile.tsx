"use client";

import Script from "next/script";
import { useId, useRef } from "react";

/**
 * Cloudflare's own script, not an npm wrapper — the widget is a handful of lines of
 * DOM glue around a global `window.turnstile.render`, so a dependency would buy nothing.
 * Renders nothing when no site key is configured (local dev): the backend's
 * TURNSTILE_SECRET_KEY is equally unset there and skips verification, so an empty
 * token round-trips fine. See contact/turnstile.py.
 */

declare global {
  interface Window {
    turnstile?: {
      render: (
        container: HTMLElement,
        options: { sitekey: string; callback: (token: string) => void; "expired-callback"?: () => void },
      ) => string;
    };
  }
}

export function Turnstile({ onVerify }: { onVerify: (token: string) => void }) {
  const siteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;
  const containerRef = useRef<HTMLDivElement>(null);
  const id = useId();

  if (!siteKey) return null;

  return (
    <>
      <div ref={containerRef} id={id} />
      <Script
        src="https://challenges.cloudflare.com/turnstile/v0/api.js"
        strategy="afterInteractive"
        onReady={() => {
          if (containerRef.current && window.turnstile) {
            window.turnstile.render(containerRef.current, {
              sitekey: siteKey,
              callback: onVerify,
              "expired-callback": () => onVerify(""),
            });
          }
        }}
      />
    </>
  );
}
