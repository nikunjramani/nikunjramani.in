#!/usr/bin/env python3
"""Generate the required-field assertions in infra/rules/firestore.rules from each
schema's x-firestore.publicRead flag and `required` list.

Firestore rules can't import anything, so without this the collection allowlist and
the per-collection required-field checks are hand-maintained prose that silently stops
matching the schemas the moment someone adds a field or a new public collection. This
regenerates only the marked block; everything else in the file (the match rule, the
security-posture comments) is hand-authored and left untouched.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "architecture" / "schemas"
OUT = ROOT / "infra" / "rules" / "firestore.rules"

BEGIN = "    // ── BEGIN GENERATED: architecture/codegen/gen-rules.py — DO NOT EDIT BY HAND ──"
END = "    // ── END GENERATED ──"


def _wrap(fields: list[str]) -> str:
    checks = [f"'{f}' in data" for f in fields]
    lines = []
    for i in range(0, len(checks), 3):
        lines.append(" && ".join(checks[i : i + 3]))
    return "\n          && ".join(lines)


def main() -> int:
    collections: dict[str, list[str]] = {}

    for path in sorted(SCHEMAS.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        meta = schema.get("x-firestore", {})
        if meta.get("publicRead") is not True:
            continue
        collection = meta.get("collection")
        if not collection:
            continue
        collections[collection] = schema.get("required", [])

    names = sorted(collections)

    body = []
    body.append(BEGIN)
    body.append(
        "    // Derived from every schema's `x-firestore.publicRead` flag and `required` list."
    )
    body.append("    // `make gen` regenerates this block; CI fails if it drifts from the schemas.")
    body.append("    // See ADR 0006 and .docs/plan/phases/phase-1-schemas.md §1.6.")
    body.append("")
    body.append("    function isPublicCollection(col) {")
    quoted = ", ".join(f"'{n}'" for n in names)
    body.append(f"      return col in [{quoted}];")
    body.append("    }")
    body.append("")
    body.append(
        "    // A publicly-readable document must carry every field its own schema requires —"
    )
    body.append(
        "    // on a doc missing one (a partial write caught mid-transaction, a bad manual"
    )
    body.append(
        "    // console edit) this evaluates to false, the read is denied, and the site"
    )
    body.append("    // renders empty rather than serving a half-written document.")
    body.append("    function hasRequiredFields(col, data) {")
    for i, name in enumerate(names):
        prefix = "return " if i == 0 else "         "
        body.append(f"      {prefix}col == '{name}' ? isComplete_{name}(data) :")
    body.append("             false;")
    body.append("    }")

    for name in names:
        body.append("")
        body.append(f"    function isComplete_{name}(data) {{")
        fields = collections[name]
        if not fields:
            body.append("      return true;")
        else:
            checks = " && ".join(f"'{f}' in data" for f in fields)
            body.append(f"      return {checks};")
        body.append("    }")

    body.append("")
    body.append(END)

    generated = "\n".join(body)

    current = OUT.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(current):
        print(f"error: {OUT} has no BEGIN/END GENERATED markers to replace", file=sys.stderr)
        return 1

    OUT.write_text(pattern.sub(generated, current), encoding="utf-8", newline="\n")
    print(f"  rules       → infra/rules/firestore.rules ({len(names)} public collections)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
