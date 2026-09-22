"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";
import type { ComponentProps } from "react";

/** A thin client wrapper is required: next-themes' provider is a Client Component, and
 * CLAUDE.md rule 5 says push "use client" as deep as possible — this is that leaf. */
export function ThemeProvider({ children, ...props }: ComponentProps<typeof NextThemesProvider>) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
