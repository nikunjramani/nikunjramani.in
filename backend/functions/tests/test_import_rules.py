"""Rules import-linter can't express precisely, checked from the source.

Only repositories talk to Firestore: a routes.py or service.py importing the SDK is the
layering bug ADR 0017 exists to prevent. (A subdomain's main.py may import Firestore *types*
for a trigger's event signature — that is the Firebase entry point, not business logic.)
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
FIRESTORE = ("google.cloud.firestore", "firebase_admin.firestore")


def _imports(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_routes_and_services_never_import_firestore() -> None:
    offenders = [
        f"{path.relative_to(BACKEND)}: {name}"
        for pattern in ("src/**/routes.py", "src/**/service.py", "kernel/crud/service.py")
        for path in BACKEND.glob(pattern)
        for name in _imports(path)
        if name.startswith(FIRESTORE)
    ]
    assert not offenders, offenders


def test_domains_import_models_only_from_shared_generated() -> None:
    """Models come from the one generated package; nothing else in shared/ exists to import."""
    offenders = [
        f"{path.relative_to(BACKEND)}: {name}"
        for path in BACKEND.glob("src/**/*.py")
        for name in _imports(path)
        if name.startswith("shared") and name != "shared.generated"
    ]
    assert not offenders, offenders


def test_layout_has_no_init_files_tests_or_common_folders() -> None:
    """The structure ADR 0017 settled on: implicit namespace packages (only the generated
    models keep an __init__.py, as their re-export), tests only under tests/, and no
    common/ grab-bag — every subdomain owns its files."""
    inits = [
        str(p.relative_to(BACKEND))
        for p in BACKEND.glob("**/__init__.py")
        if "generated" not in p.parts and ".venv" not in p.parts and "venv" not in p.parts
    ]
    misplaced_tests = [
        str(p.relative_to(BACKEND))
        for root in ("src", "kernel", "shared")
        for p in (BACKEND / root).glob("**/test_*.py")
    ]
    common_dirs = [str(p.relative_to(BACKEND)) for p in (BACKEND / "src").glob("**/common")]
    assert not inits, inits
    assert not misplaced_tests, misplaced_tests
    assert not common_dirs, common_dirs
