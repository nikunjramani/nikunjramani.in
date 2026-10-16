/**
 * RFC 7386 merge patch from the document as loaded to the values as edited.
 *
 * Sending the edited values themselves as the patch can't remove anything: a cleared field
 * is `undefined` in the form, `JSON.stringify` drops it, and the server keeps the old value.
 * A removal has to be an explicit `null`, which is what this produces — and unchanged keys
 * are left out entirely. Objects recurse; arrays and scalars replace wholesale, matching
 * shared/crud.py's deep_merge.
 */
type Json = Record<string, unknown>;

export function toMergePatch(original: Json, edited: Json): Json {
  const before = prune(original) as Json | undefined;
  const after = prune(edited) as Json | undefined;
  return diff(before ?? {}, after ?? {});
}

function diff(before: Json, after: Json): Json {
  const patch: Json = {};
  for (const key of new Set([...Object.keys(before), ...Object.keys(after)])) {
    const was = before[key];
    const now = after[key];
    if (now === undefined) {
      if (was !== undefined) patch[key] = null;
    } else if (isObject(was) && isObject(now)) {
      const nested = diff(was, now);
      if (Object.keys(nested).length) patch[key] = nested;
    } else if (!deepEqual(was, now)) {
      patch[key] = now;
    }
  }
  return patch;
}

/** Drop null/undefined and objects left with no keys — "an empty section" is "no section". */
function prune(value: unknown): unknown {
  if (value === null || value === undefined) return undefined;
  if (Array.isArray(value)) return value.map((item) => prune(item) ?? null);
  if (isObject(value)) {
    const entries = Object.entries(value)
      .map(([k, v]) => [k, prune(v)] as const)
      .filter(([, v]) => v !== undefined);
    return entries.length ? Object.fromEntries(entries) : undefined;
  }
  return value;
}

function isObject(value: unknown): value is Json {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function deepEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (Array.isArray(a) && Array.isArray(b)) {
    return a.length === b.length && a.every((item, i) => deepEqual(item, b[i]));
  }
  if (isObject(a) && isObject(b)) {
    const keys = Object.keys(a);
    return keys.length === Object.keys(b).length && keys.every((k) => deepEqual(a[k], b[k]));
  }
  return false;
}
