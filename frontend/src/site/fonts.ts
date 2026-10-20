import { Archivo, IBM_Plex_Mono } from "next/font/google";

// Self-hosted at build time by next/font (FE-20). Archivo is variable on weight *and* width:
// body text sets at normal width, headings stretch wider (`font-stretch-*`) — one family doing
// the work of two. Plex Mono carries the spec-sheet data: keys, dates, figures (FE-23).
const sans = Archivo({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
  axes: ["wdth"],
});
const mono = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
  weight: ["400", "500"],
});

export const fontVariables = `${sans.variable} ${mono.variable}`;
