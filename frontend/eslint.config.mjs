import coreWebVitals from "eslint-config-next/core-web-vitals";
import typescript from "eslint-config-next/typescript";

const eslintConfig = [
  ...coreWebVitals,
  ...typescript,
  {
    ignores: ["src/generated/**", ".next/**", "node_modules/**", "next-env.d.ts"],
  },
  {
    // Bundle boundary: the admin editor, its form renderer and the Firebase client SDK
    // must never ship to a visitor reading a project page. See CLAUDE.md rule 5.
    files: ["src/app/(site)/**/*.{ts,tsx}", "src/components/site/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["**/(admin)/**", "@/components/admin/*", "@/lib/api/*"],
              message:
                "Public site code must not import admin code — it would ship the admin bundle to visitors.",
            },
          ],
        },
      ],
    },
  },
];

export default eslintConfig;
