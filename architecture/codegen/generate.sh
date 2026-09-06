#!/usr/bin/env bash
# Regenerate every model from architecture/schemas. Wired up in Phase 1.
#
# Targets: Pydantic v2 (backend), TypeScript types (frontend), Zod validators (admin forms).
# Output is committed but NEVER hand-edited — CI runs this and fails on any diff.
set -euo pipefail

cd "$(dirname "$0")/../.."

if [ -z "$(find architecture/schemas -name '*.schema.json' 2>/dev/null)" ]; then
  echo "No schemas yet — this gets implemented in Phase 1."
  echo "See docs/plan/phases/phase-1-schemas.md"
  exit 0
fi

echo "Phase 1 not implemented yet."
exit 0
