/**
 * Dereference a schema into a single self-contained document.
 *
 * json-schema-to-zod does NOT follow cross-file $refs — it silently emits z.any() for
 * every referenced field. That produces a validator that looks right and accepts anything,
 * which is worse than no validator at all. So every schema is dereferenced first.
 */
import { writeFile } from "node:fs/promises";
import $RefParser from "@apidevtools/json-schema-ref-parser";

const [input, output] = process.argv.slice(2);
if (!input || !output) {
  console.error("usage: node deref.mjs <input.schema.json> <output.json>");
  process.exit(1);
}

const schema = await $RefParser.dereference(input);
await writeFile(output, JSON.stringify(schema, null, 2));
