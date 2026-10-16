/** "readingMinutes" → "Reading Minutes". */
export function fieldLabel(key: string): string {
  const spaced = key.replace(/([A-Z])/g, " $1");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

/**
 * An untouched or cleared HTML input's value is "", not undefined. For an optional field
 * that "" either fails a Zod format/enum check before `.optional()` gets a say (url,
 * pattern, enum), or gets stored as an empty string instead of the field being removed.
 * "Empty means absent" is the rule for every form control.
 */
export function emptyToUndefined(value: unknown): unknown {
  return value === "" ? undefined : value;
}

export const inputClass =
  "rounded-md border border-border bg-background px-3 py-2 text-sm focus-visible:outline-2 focus-visible:outline-accent";
