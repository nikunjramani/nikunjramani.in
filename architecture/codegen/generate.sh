#!/usr/bin/env bash
# Regenerate every model from architecture/schemas.
#
# Targets: Pydantic v2 (backend), TypeScript types + Zod validators (frontend).
# Output is committed but NEVER hand-edited — CI runs this and fails on any diff. ADR 0006.
set -euo pipefail

cd "$(dirname "$0")/../.."
ROOT="$PWD"
SCHEMAS="$ROOT/architecture/schemas"
PY_OUT="$ROOT/backend/functions/shared/generated"

if ! compgen -G "$SCHEMAS/*.schema.json" > /dev/null; then
  echo "No schemas yet — nothing to generate."
  exit 0
fi

echo "▶ generating from architecture/schemas"

# ── Python: Pydantic v2 ─────────────────────────────────────────────
rm -rf "$PY_OUT"
uvx --quiet --from datamodel-code-generator datamodel-codegen \
  --input "$SCHEMAS" \
  --input-file-type jsonschema \
  --output "$PY_OUT" \
  --output-model-type pydantic_v2.BaseModel \
  --target-python-version 3.13 \
  --use-standard-collections \
  --use-union-operator \
  --use-schema-description \
  --use-field-description \
  --use-default-kwarg \
  --disable-timestamp

# A curated re-export, so callers write `from shared.generated import Project` rather than
# `from shared.generated.project_schema import Project`. Generated, not hand-edited.
{
  echo '"""DO NOT EDIT. Generated from architecture/schemas by `make gen`. See ADR 0006."""'
  echo
  for f in "$SCHEMAS"/*.schema.json; do
    base="$(basename "$f" .schema.json)"
    module="$(echo "$base" | tr '-' '_')_schema"
    title="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['title'])" "$f")"
    echo "from .${module} import ${title} as ${title}"
  done
  echo
  echo '__all__ = ['
  for f in "$SCHEMAS"/*.schema.json; do
    title="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['title'])" "$f")"
    echo "    \"${title}\","
  done
  echo ']'
} > "$PY_OUT/__init__.py"

echo "  pydantic    → backend/functions/shared/generated/"

# ── TypeScript + Zod ────────────────────────────────────────────────
cd "$ROOT/architecture/codegen"
[ -d node_modules ] || npm install --silent
node gen-frontend.mjs

# ── Firestore indexes ───────────────────────────────────────────────
python3 "$ROOT/architecture/codegen/gen-indexes.py"
python3 "$ROOT/architecture/codegen/gen-docs.py"

echo "✓ done"
