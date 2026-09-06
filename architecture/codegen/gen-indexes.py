#!/usr/bin/env python3
"""Generate infra/rules/firestore.indexes.json from each schema's x-firestore.indexes.

Composite queries need composite indexes, and in production a missing one is a runtime
error rather than a warning. Deriving them from the schema means the index is added when
the field is, not when production throws.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "architecture" / "schemas"
OUT = ROOT / "infra" / "rules" / "firestore.indexes.json"


def main() -> int:
    indexes: list[dict[str, object]] = []
    ttl_overrides: list[dict[str, object]] = []

    for path in sorted(SCHEMAS.glob("*.schema.json")):
        schema = json.loads(path.read_text())
        meta = schema.get("x-firestore", {})
        collection = meta.get("collection")
        if not collection:
            continue

        for fields in meta.get("indexes", []):
            indexes.append(
                {
                    "collectionGroup": collection,
                    "queryScope": "COLLECTION",
                    "fields": [
                        {"fieldPath": f, "order": "ASCENDING"} for f in fields
                    ],
                }
            )

        if ttl_field := meta.get("ttlField"):
            ttl_overrides.append(
                {
                    "collectionGroup": collection,
                    "fieldPath": ttl_field,
                    "ttl": True,
                    "indexes": [],
                }
            )

    payload = {"indexes": indexes, "fieldOverrides": ttl_overrides}
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"  indexes     → infra/rules/firestore.indexes.json ({len(indexes)} indexes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
