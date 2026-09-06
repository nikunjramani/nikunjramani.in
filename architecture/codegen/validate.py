#!/usr/bin/env python3
"""Validate every schema, and every example fixture against its schema.

The invalid fixtures matter more than the valid ones. A schema that accepts anything
passes all the valid examples too — only the invalid ones prove it is actually
constraining something.

Run with: make validate
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "architecture" / "schemas"
EXAMPLES = ROOT / "architecture" / "examples"

GREEN, RED, DIM, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[0m"


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def build_registry() -> Registry:
    """Register every schema under a path relative to schemas/, so `$ref`s resolve."""
    registry: Registry = Registry()
    for path in SCHEMAS.rglob("*.json"):
        rel = path.relative_to(SCHEMAS).as_posix()
        resource = Resource.from_contents(load(path), default_specification=DRAFT202012)
        registry = registry.with_resource(uri=rel, resource=resource)
    return registry


def validator_for(name: str, registry: Registry) -> Draft202012Validator:
    # Relative $refs resolve against each schema's own $id, which is why every schema
    # declares one matching its path under schemas/.
    schema = load(SCHEMAS / f"{name}.schema.json")
    return Draft202012Validator(schema, registry=registry)


def main() -> int:
    roots = sorted(SCHEMAS.glob("*.schema.json"))
    if not roots:
        print("No schemas yet — nothing to validate.")
        return 0

    registry = build_registry()
    failures: list[str] = []

    # ── 1 · every schema is itself a valid JSON Schema ──────────────
    print(f"{DIM}schemas{RESET}")
    for path in sorted(SCHEMAS.rglob("*.json")):
        rel = path.relative_to(SCHEMAS)
        try:
            Draft202012Validator.check_schema(load(path))
            print(f"  {GREEN}✓{RESET} {rel}")
        except Exception as exc:
            print(f"  {RED}✗{RESET} {rel}: {exc}")
            failures.append(str(rel))

    # ── 2 · valid fixtures must pass ────────────────────────────────
    print(f"\n{DIM}valid fixtures — must pass{RESET}")
    for path in sorted((EXAMPLES / "valid").glob("*.json")):
        data = load(path)
        name = data.pop("$schema", None)
        data.pop("_why", None)
        if not name:
            print(f"  {RED}✗{RESET} {path.name}: missing \"$schema\" marker")
            failures.append(path.name)
            continue
        errors = list(validator_for(name, registry).iter_errors(data))
        if errors:
            print(f"  {RED}✗{RESET} {path.name}: {errors[0].message}")
            failures.append(path.name)
        else:
            print(f"  {GREEN}✓{RESET} {path.name}")

    # ── 3 · invalid fixtures must FAIL ──────────────────────────────
    print(f"\n{DIM}invalid fixtures — must be rejected{RESET}")
    for path in sorted((EXAMPLES / "invalid").glob("*.json")):
        data = load(path)
        name = data.pop("$schema", None)
        why = data.pop("_why", "")
        errors = list(validator_for(name, registry).iter_errors(data))
        if errors:
            print(f"  {GREEN}✓{RESET} {path.name} {DIM}— rejected: {errors[0].message[:70]}{RESET}")
        else:
            print(f"  {RED}✗{RESET} {path.name} was ACCEPTED but should not be")
            print(f"      {DIM}{why}{RESET}")
            failures.append(path.name)

    print()
    if failures:
        print(f"{RED}✗ {len(failures)} failure(s){RESET}")
        return 1
    print(f"{GREEN}✓ all schemas and fixtures pass{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
