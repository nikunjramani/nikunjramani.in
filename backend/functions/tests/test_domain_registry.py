"""Every hand-maintained list of domains and subdomains, checked against the code on disk.

A new subdomain is registered in its domain's FUNCTIONS table (main.py), the import-linter
contracts, next.config.ts's rewrites and the Terraform invoker list. Missing any one fails
silently in production — no deploy, unchecked boundaries, a frontend 404, a Cloud Run 403
— so this test reads them all and demands they agree with src/.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from main import FUNCTIONS
from src.ops.backup.service import BACKED_UP_COLLECTIONS

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _subdomains() -> set[tuple[str, str]]:
    """(domain, subdomain) for every src/<domain>/<subdomain>/ — a subdomain is a folder
    with a main.py entry point."""
    return {(p.parent.parent.name, p.parent.name) for p in (BACKEND / "src").glob("*/*/main.py")}


def _http_functions() -> dict[str, str]:
    return {name: module for name, module in FUNCTIONS.items() if name.startswith("api_")}


def test_every_subdomain_has_a_main_that_defines_a_listed_function() -> None:
    listed_modules = set(FUNCTIONS.values())
    for domain, sub in _subdomains():
        assert f"src.{domain}.{sub}.main" in listed_modules, f"{domain}/{sub} deploys nothing"


def test_http_functions_are_named_after_their_subdomain() -> None:
    for name, module in _http_functions().items():
        _, domain, sub, _ = module.split(".")
        assert name == f"api_{domain}_{sub}", (name, module)


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


def test_next_config_rewrites_every_http_function() -> None:
    source = _read(REPO / "frontend" / "next.config.ts")
    block = re.search(r"const ROUTES = \[(.*?)\]", source, re.DOTALL)
    assert block, "ROUTES array not found in next.config.ts"
    rewritten = set(re.findall(r'"(\w+/\w+)"', block.group(1)))
    assert {"api_" + r.replace("/", "_") for r in rewritten} == set(_http_functions())


def test_terraform_grants_invoker_on_every_http_function() -> None:
    source = _read(REPO / "infra" / "terraform" / "modules" / "functions" / "main.tf")
    block = re.search(r'variable "http_functions" \{.*?default = \[(.*?)\]', source, re.DOTALL)
    assert block, "http_functions default not found"
    assert set(re.findall(r'"(api_\w+)"', block.group(1))) == set(_http_functions())


def test_backup_covers_every_collection_the_schemas_declare() -> None:
    declared = set()
    for path in (REPO / "architecture" / "schemas").glob("*.schema.json"):
        collection = json.loads(_read(path)).get("x-firestore", {}).get("collection")
        if collection:
            declared.add(collection)
    assert declared <= set(BACKED_UP_COLLECTIONS)
