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
  // Without this, every maxItems-constrained array (common/*.schema.json uses it
  // throughout) compiles to a union of fixed-length tuples — one variant per length up
  // to the max — instead of a plain T[]. On project.schema.json alone that inflated the
  // output from a few hundred lines to nearly 3,700. maxLength/minLength on strings are
  // unaffected; this option is specifically about array length bounds.
  ignoreMinAndMaxItems: true,
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

// ── Admin form schemas ──────────────────────────────────────────────
// <SchemaForm> (Phase 5) reads these at runtime to build the admin editor for every
// content collection — field resolver walks `schema.properties`, so a field added here
// needs no form code changed. Only `x-firestore.publicRead: true` schemas get a generic
// form: that flag already exactly identifies the 8 collections shared/crud.py's generic
// router serves (media-asset, contact-message and audit-log are all publicRead: false —
// each has its own hand-built admin UI instead, for reasons documented in their own
// service.py files).
//
// One exception the schema can't tell you: `x-firestore.collection` is the Firestore
// collection name, but the site-config domain's API route is mounted as `/settings`, not
// `/site_config` — see backend/functions/src/settings/. Every other domain's route matches
// its collection name exactly.
const API_DOMAIN_OVERRIDES = { site_config: "settings" };

const formSchemas = {};
for (const file of roots) {
  const raw = JSON.parse(
    await (await import("node:fs/promises")).readFile(path.join(SCHEMAS, file), "utf8"),
  );
  if (raw["x-firestore"]?.publicRead !== true) continue;

  const deref = await $RefParser.dereference(path.join(SCHEMAS, file));
  const collection = raw["x-firestore"].collection;
  const required = deref.required ?? [];

  formSchemas[pascal(file)] = {
    title: deref.title,
    collection,
    apiDomain: API_DOMAIN_OVERRIDES[collection] ?? collection,
    // Matches shared/crud.py's make_crud_router(slugged=...): the document id is the
    // payload's own `slug` field rather than an auto-generated one.
    slugged: required.includes("slug"),
    // Matches make_crud_router(singleton_id="main"): one fixed document, no list/create/
    // delete/reorder — profile and site-config are the only two.
    singleton: collection === "profile" || collection === "site_config",
    required,
    properties: deref.properties,
  };
}

await writeFile(
  path.join(OUT, "admin-schemas.ts"),
  await prettier.format(
    `${BANNER}import type { JSONSchema7 } from "json-schema";

export interface AdminSchemaEntry {
  title: string;
  collection: string;
  apiDomain: string;
  slugged: boolean;
  singleton: boolean;
  required: string[];
  properties: Record<string, JSONSchema7>;
}

export const ADMIN_SCHEMAS = ${JSON.stringify(formSchemas)} as const satisfies Record<string, AdminSchemaEntry>;
`,
    { parser: "typescript" },
  ),
);

console.log(
  `  admin forms → frontend/src/generated/admin-schemas.ts (${Object.keys(formSchemas).length} collections)`,
);
