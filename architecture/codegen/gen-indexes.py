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

# Collections with no schema that still need a TTL: rate-limit windows are written with an
# `expiresAt` and would otherwise accumulate forever (see shared/core/rate_limit.py).
INTERNAL_TTL = [("_rate_limits", "expiresAt")]


def _field(spec: str) -> dict[str, str]:
    """`"at"` is ascending, `"at:desc"` descending, `"tags:contains"` an array-contains
    entry. A composite index only serves an order_by in the direction it was built with."""
    path, _, mode = spec.partition(":")
    if mode == "contains":
        return {"fieldPath": path, "arrayConfig": "CONTAINS"}
    return {"fieldPath": path, "order": "DESCENDING" if mode == "desc" else "ASCENDING"}
SCHEMAS = ROOT / "architecture" / "schemas"
OUT = ROOT / "infra" / "rules" / "firestore.indexes.json"


def main() -> int:
    indexes: list[dict[str, object]] = []
    ttl_overrides: list[dict[str, object]] = []

    for path in sorted(SCHEMAS.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        meta = schema.get("x-firestore", {})
        collection = meta.get("collection")
        if not collection:
            continue

        for fields in meta.get("indexes", []):
            if len(fields) < 2:
                # Firestore auto-manages single-field indexes via single-field index
                # controls — the Admin API rejects a composite index entry with only
                # one field ("not necessary, configure using single field index
                # controls"). Only 2+ field combinations need to go here.
                continue
            indexes.append(
                {
                    "collectionGroup": collection,
                    "queryScope": "COLLECTION",
                    "fields": [_field(f) for f in fields],
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

    for collection, ttl_field in INTERNAL_TTL:
        ttl_overrides.append(
            {"collectionGroup": collection, "fieldPath": ttl_field, "ttl": True, "indexes": []}
        )

    payload = {"indexes": indexes, "fieldOverrides": ttl_overrides}
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"  indexes     → infra/rules/firestore.indexes.json ({len(indexes)} indexes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
