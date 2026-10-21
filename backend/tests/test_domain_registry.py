"""Every hand-maintained list of domains and subdomains, checked against the code on disk.

A new subdomain is registered in apps/api.py (mounted, or nothing serves it) and in
architecture/api-routes.json (the frontend's route names), and its folder must appear in the
import-linter contracts. Missing any one fails silently — a 404, a frontend calling a route
that isn't there, unchecked boundaries — so this test reads them all and demands they agree
with src/.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from apps.api import API_PREFIX, INTERNAL, ROUTES, app
from src.media.library.repository import CONTENT_COLLECTIONS
from src.ops.backup.service import BACKED_UP_COLLECTIONS

BACKEND = Path(__file__).resolve().parents[1]
REPO = next(p for p in BACKEND.parents if (p / "architecture").is_dir())


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _subdomains() -> set[tuple[str, str]]:
    """(domain, subdomain) for every src/<domain>/<subdomain>/ that has an entry point — an
    HTTP router (routes.py) or an event router (events.py)."""
    return {
        (p.parent.parent.name, p.parent.name)
        for name in ("routes.py", "events.py")
        for p in (BACKEND / "src").glob(f"*/*/{name}")
    }


def _with(entry: str) -> set[str]:
    return {
        f"{p.parent.parent.name}/{p.parent.name}" for p in (BACKEND / "src").glob(f"*/*/{entry}")
    }


def test_every_routes_py_is_mounted_and_nothing_else_is() -> None:
    assert set(ROUTES) == _with("routes.py")


def test_every_events_py_is_mounted_under_internal() -> None:
    assert set(INTERNAL) == _with("events.py")
    assert all(prefix.startswith("/internal/") for prefix, _ in INTERNAL.values())


def test_api_routes_manifest_matches_the_mounted_routers() -> None:
    manifest = json.loads(_read(REPO / "architecture" / "api-routes.json"))
    assert {route for domain in manifest.values() for route in domain.values()} == set(ROUTES)


def test_each_router_is_served_at_its_prefix() -> None:
    # The OpenAPI schema lists every served path; app.routes keeps included routers nested.
    paths = set(app.openapi()["paths"])
    for route in ROUTES:
        prefix = f"{API_PREFIX}/{route}"
        assert any(p == prefix or p.startswith(f"{prefix}/") for p in paths), route


def test_import_linter_contracts_cover_every_domain_and_subdomain() -> None:
    config = tomllib.loads(_read(BACKEND / "pyproject.toml"))
    contracts = config["tool"]["importlinter"]["contracts"]
    independent = [set(c["modules"]) for c in contracts if c["type"] == "independence"]

    domains = {d for d, _ in _subdomains()}
    assert {f"src.{d}" for d in domains} in independent

    for domain in domains:
        subs = {f"src.{domain}.{s}" for d, s in _subdomains() if d == domain}
        if len(subs) > 1:
            assert subs in independent, f"no independence contract for {domain}'s subdomains"

    layered = next(c for c in contracts if c["type"] == "layers")
    assert {f"src.{d}.{s}" for d, s in _subdomains()} == set(layered["containers"])


def test_next_config_rewrites_the_api_prefix() -> None:
    next_config = _read(REPO / "frontend" / "next.config.ts")
    assert 'from "./src/lib/backend"' in next_config
    assert "`${API_PREFIX}/:path*`" in next_config


def test_backup_covers_every_collection_the_schemas_declare() -> None:
    declared = set()
    for path in (REPO / "architecture" / "schemas").glob("*.schema.json"):
        collection = json.loads(_read(path)).get("x-firestore", {}).get("collection")
        if collection:
            declared.add(collection)
    assert declared <= set(BACKED_UP_COLLECTIONS)


def test_media_usage_scans_every_content_collection() -> None:
    """A content collection missing here would let an image it uses be deleted unwarned."""
    public = set()
    for path in (REPO / "architecture" / "schemas").glob("*.schema.json"):
        meta = json.loads(_read(path)).get("x-firestore", {})
        if meta.get("publicRead") is True:
            public.add(meta["collection"])
    assert public == set(CONTENT_COLLECTIONS)
