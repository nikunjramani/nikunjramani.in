import coreWebVitals from "eslint-config-next/core-web-vitals";
import typescript from "eslint-config-next/typescript";

// Surface boundaries (ADR 0021). Dependencies point one way:
//   site  ─┐
//          ├─►  shared · lib · generated
//   admin ─┘    (admin may also import site components — the editor previews with them)
const ADMIN_CODE = {
  group: ["**/(admin)/**", "@/admin/*", "@/admin/**"],
  message:
    "Public site code must not import admin code — it would ship the admin bundle to visitors.",
};
// All data goes through the Python API (ADR 0022) — no Firestore SDK anywhere in the frontend.
const FIRESTORE = {
  group: ["firebase-admin/firestore", "firebase/firestore", "@google-cloud/firestore"],
  message: "The frontend never touches Firestore — read through lib/data (the Python API), write through admin/api-client.",
};
const SURFACE_CODE = {
  group: ["**/(site)/**", "**/(admin)/**", "@/site/*", "@/site/**", "@/admin/*", "@/admin/**"],
  message: "Shared code (shared/, lib/) must not depend on either surface — move it to the surface that uses it.",
};

const eslintConfig = [
  ...coreWebVitals,
  ...typescript,
  {
    ignores: ["src/generated/**", ".next/**", "node_modules/**", "next-env.d.ts"],
  },
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: { "no-restricted-imports": ["error", { patterns: [FIRESTORE] }] },
  },
  // A later block's no-restricted-imports replaces an earlier one's, so each repeats FIRESTORE.
  {
    files: ["src/app/(site)/**/*.{ts,tsx}", "src/site/**/*.{ts,tsx}", "src/app/global-not-found.tsx"],
    rules: { "no-restricted-imports": ["error", { patterns: [ADMIN_CODE, FIRESTORE] }] },
  },
  {
    files: ["src/shared/**/*.{ts,tsx}", "src/lib/**/*.{ts,tsx}"],
    rules: { "no-restricted-imports": ["error", { patterns: [SURFACE_CODE, FIRESTORE] }] },
  },
];

export default eslintConfig;
