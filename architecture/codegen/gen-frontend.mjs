/**
 * Generates the frontend's TypeScript types and Zod validators from architecture/schemas.
 *
 * Types come from json-schema-to-typescript, which resolves $refs itself. Zod validators
 * come from json-schema-to-zod, which does NOT — it silently emits z.any() for referenced
 * fields, so every schema is dereferenced first. A validator that looks right and accepts
 * anything is worse than no validator.
 */
import { readdir, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

import $RefParser from "@apidevtools/json-schema-ref-parser";
import { compile } from "json-schema-to-typescript";
import { jsonSchemaToZod } from "json-schema-to-zod";
import prettier from "prettier";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SCHEMAS = path.resolve(HERE, "../schemas");
const OUT = path.resolve(HERE, "../../frontend/src/generated");

const BANNER = `/**
 * DO NOT EDIT. Generated from architecture/schemas by \`make gen\`.
 * CI regenerates this and fails on any diff. See ADR 0006.
 */
/* eslint-disable */
`;

const pascal = (file) =>
  file
    .replace(/\.schema\.json$/, "")
    .split("-")
    .map((s) => s[0].toUpperCase() + s.slice(1))
    .join("");

const roots = (await readdir(SCHEMAS))
  .filter((f) => f.endsWith(".schema.json"))
  .sort();

if (roots.length === 0) {
  console.log("  no schemas yet — nothing to generate");
  process.exit(0);
}

await mkdir(OUT, { recursive: true });

// ── TypeScript ──────────────────────────────────────────────────────
// One combined document so shared types (Media, Link, Metric) are emitted once
// rather than duplicated into every model's file.
const combined = {
  $schema: "https://json-schema.org/draft/2020-12/schema",
  title: "Models",
  type: "object",
  properties: Object.fromEntries(
    roots.map((f) => [pascal(f), { $ref: f }]),
  ),
  additionalProperties: false,
};

let ts = await compile(combined, "Models", {
  cwd: SCHEMAS + path.sep,
  bannerComment: "",
  additionalProperties: false,
  declareExternallyReferenced: true,
  unreachableDefinitions: false,
  style: { singleQuote: false },
});

// The wrapper interface exists only to pull every model into one file.
ts = ts.replace(/export interface Models \{[\s\S]*?\n\}\n/, "");

await writeFile(
  path.join(OUT, "types.ts"),
  await prettier.format(BANNER + ts, { parser: "typescript" }),
);

// ── Zod ─────────────────────────────────────────────────────────────
const parts = [BANNER, 'import { z } from "zod";\n'];

for (const file of roots) {
  const deref = await $RefParser.dereference(path.join(SCHEMAS, file));
  const name = pascal(file);
  const body = jsonSchemaToZod(deref, { module: "none" });
  parts.push(`\nexport const ${name}Schema = ${body};\n`);
  parts.push(
    `export type ${name}Input = z.infer<typeof ${name}Schema>;\n`,
  );
}

await writeFile(
  path.join(OUT, "schemas.zod.ts"),
  await prettier.format(parts.join(""), { parser: "typescript" }),
);

console.log(`  typescript  → frontend/src/generated/types.ts (${roots.length} models)`);
console.log(`  zod         → frontend/src/generated/schemas.zod.ts`);
