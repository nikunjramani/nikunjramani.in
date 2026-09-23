import type { JSONSchema7 } from "json-schema";

/**
 * Schema type -> control. This is the whole reason a schema field shows up in the admin
 * form with no form code touched (see architecture/codegen/gen-frontend.mjs's own comment
 * on ADMIN_SCHEMAS, and the plan's "test 6"): every property gets walked and classified
 * here, purely from its JSON Schema shape, not from a hardcoded per-field list.
 */
export type FieldKind =
  | "text"
  | "textarea"
  | "markdown"
  | "number"
  | "boolean"
  | "select"
  | "url"
  | "date"
  | "month"
  | "tags"
  | "media"
  | "object"
  | "array-of-objects"
  | "array-of-strings"
  | "unknown";

export interface ResolvedField {
  key: string;
  kind: FieldKind;
  schema: JSONSchema7;
  required: boolean;
}

const MEDIA_KEYS = new Set(["url", "alt", "caption", "type", "width", "height", "blurhash"]);

/** common/media.schema.json, once dereferenced, is a plain object with exactly this shape —
 * there's no `$ref` left to key off after dereferencing, so structural shape is the only
 * signal available. url+alt are its two required fields; everything else it might carry is
 * a subset of MEDIA_KEYS. */
function looksLikeMedia(schema: JSONSchema7): boolean {
  if (schema.type !== "object" || !schema.properties) return false;
  const keys = Object.keys(schema.properties);
  if (!keys.includes("url") || !keys.includes("alt")) return false;
  return keys.every((k) => MEDIA_KEYS.has(k));
}

// Fields whose *content* is prose meant to render as Markdown on the public site (see each
// schema's own description — profile.bio, project.content.overview/problem/approach), not
// just "a long string". maxLength alone can't distinguish a long plain-text field from a
// long Markdown one, so the field name carries the rest of the signal.
const MARKDOWN_FIELD_NAMES = new Set(["bio", "overview", "problem", "approach", "description"]);

export function resolveField(key: string, schema: JSONSchema7, required: boolean): ResolvedField {
  const kind = classify(key, schema);
  return { key, kind, schema, required };
}

function classify(key: string, schema: JSONSchema7): FieldKind {
  if (looksLikeMedia(schema)) return "media";

  if (schema.type === "boolean") return "boolean";
  if (schema.type === "integer" || schema.type === "number") return "number";

  if (schema.type === "object") return "object";

  if (schema.type === "array") {
    const items = schema.items;
    const itemSchema = Array.isArray(items) ? items[0] : items;
    if (itemSchema && typeof itemSchema === "object") {
      if (itemSchema.type === "object") return "array-of-objects";
      if (itemSchema.type === "string") return "array-of-strings";
    }
    return "unknown";
  }

  if (schema.type === "string" || (Array.isArray(schema.type) && schema.type.includes("string"))) {
    if (schema.enum) return "select";
    if (schema.format === "uri") return "url";
    if (schema.format === "date-time") return "date";
    if (schema.pattern === "^\\d{4}-\\d{2}$") return "month";
    if (MARKDOWN_FIELD_NAMES.has(key)) return "markdown";
    const maxLength = schema.maxLength ?? 0;
    if (maxLength > 200) return "textarea";
    return "text";
  }

  return "unknown";
}

/** Server-managed fields never belong in a form — nothing the admin panel submits should
 * be able to override them (audit stamps createdAt/updatedAt/publishedAt/createdBy itself
 * in shared/crud.py; slug becomes the document id at create time and is immutable after). */
const OMITTED_FIELDS = new Set(["audit"]);

export function formFieldEntries(
  properties: Record<string, JSONSchema7>,
  required: string[],
): ResolvedField[] {
  const requiredSet = new Set(required);
  return Object.entries(properties)
    .filter(([key]) => !OMITTED_FIELDS.has(key))
    .map(([key, schema]) => resolveField(key, schema, requiredSet.has(key)));
}
