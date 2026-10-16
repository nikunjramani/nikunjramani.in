import { ArrayOfObjectsField } from "./array-field";
import { MarkdownField } from "./markdown-field";
import { MediaField } from "./media-field";
import { ObjectSection } from "./object-section";
import {
  BooleanField,
  DateField,
  MonthField,
  NumberField,
  SelectField,
  TagsField,
  TextField,
  TextareaField,
  UrlField,
} from "./primitive-fields";
import type { ResolvedField } from "./resolve-field";

/** The single dispatch point every control-kind resolver output funnels through —
 * object and array-of-objects recurse back into this via ObjectSection / ArrayOfObjectsField,
 * so nesting to any depth needs no special-casing here. */
export function FieldRenderer({ name, field }: { name: string; field: ResolvedField }) {
  switch (field.kind) {
    case "text":
      return <TextField name={name} field={field} />;
    case "textarea":
      return <TextareaField name={name} field={field} />;
    case "markdown":
      return <MarkdownField name={name} field={field} />;
    case "number":
      return <NumberField name={name} field={field} />;
    case "boolean":
      return <BooleanField name={name} field={field} />;
    case "select":
      return <SelectField name={name} field={field} />;
    case "url":
      return <UrlField name={name} field={field} />;
    case "date":
      return <DateField name={name} field={field} />;
    case "month":
      return <MonthField name={name} field={field} />;
    case "tags":
    case "array-of-strings":
      return <TagsField name={name} field={field} />;
    case "media":
      return <MediaField name={name} field={field} />;
    case "object":
      return <ObjectSection name={name} field={field} />;
    case "array-of-objects":
      return <ArrayOfObjectsField name={name} field={field} />;
    case "unknown":
      return null;
    default:
      return null;
  }
}
