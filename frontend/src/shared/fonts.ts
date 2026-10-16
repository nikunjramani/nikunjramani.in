import { Geist, Geist_Mono } from "next/font/google";

// next/font/google downloads and self-hosts these at *build* time — the app never makes a
// runtime request to Google's CDN. That's the actual requirement (no third-party request,
// no flash of unstyled text), not a ban on ever having touched a Google-hosted font file.
// Declared once here so every root layout (site, admin, global 404) shares the same files.
const sans = Geist({ variable: "--font-sans", subsets: ["latin"], display: "swap" });
const mono = Geist_Mono({ variable: "--font-mono", subsets: ["latin"], display: "swap" });

export const fontVariables = `${sans.variable} ${mono.variable}`;
