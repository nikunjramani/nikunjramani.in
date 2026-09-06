#!/usr/bin/env python3
"""Validate every schema, and every example fixture against its schema.

The invalid fixtures matter more than the valid ones: a schema that accepts anything
passes all the valid examples too. Wired up in Phase 1.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "architecture" / "schemas"


def main() -> int:
    schemas = list(SCHEMAS.rglob("*.schema.json"))
    if not schemas:
        print("No schemas yet — this gets implemented in Phase 1.")
        print("See docs/plan/phases/phase-1-schemas.md")
        return 0

    print("Phase 1 not implemented yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
