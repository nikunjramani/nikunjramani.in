#!/usr/bin/env python3
"""Generate architecture/docs/ERD.md from the schemas — documentation that cannot go stale."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "architecture" / "schemas"
OUT = ROOT / "architecture" / "docs" / "ERD.md"


def type_of(prop: dict) -> str:
    if "$ref" in prop:
        return Path(prop["$ref"]).name.replace(".schema.json", "").replace(".json", "")
    t = prop.get("type", "any")
    if isinstance(t, list):
        return " | ".join(t)
    if t == "array":
        items = prop.get("items", {})
        return f"{type_of(items)}[]"
    return str(t)


def main() -> int:
    roots = sorted(SCHEMAS.glob("*.schema.json"))
    if not roots:
        print("No schemas yet.")
        return 0

    lines = [
        "# Data Model — generated",
        "",
        "> DO NOT EDIT. Generated from `architecture/schemas` by `make gen`.",
        "> Edit the schemas instead.",
        "",
        "## Collections",
        "",
        "| Collection | Model | Public read | Required fields | Indexes |",
        "|---|---|---|---|---|",
    ]

    for path in roots:
        s = json.loads(path.read_text())
        meta = s.get("x-firestore", {})
        req = ", ".join(f"`{r}`" for r in s.get("required", [])) or "—"
        lines.append(
            f"| `{meta.get('collection', '—')}` | **{s['title']}** | "
            f"{'✅' if meta.get('publicRead') else '❌'} | {req} | {len(meta.get('indexes', []))} |"
        )

    for path in roots:
        s = json.loads(path.read_text())
        required = set(s.get("required", []))
        lines += ["", f"## {s['title']}", ""]
        if desc := s.get("description"):
            lines += [f"_{desc}_", ""]
        lines += ["| Field | Type | Required |", "|---|---|---|"]
        for name, prop in s.get("properties", {}).items():
            mark = "**yes**" if name in required else "no"
            lines.append(f"| `{name}` | {type_of(prop)} | {mark} |")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"  docs        → architecture/docs/ERD.md ({len(roots)} models)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
