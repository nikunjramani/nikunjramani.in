"""Every list of domains that has to be maintained by hand, checked against each other.

Adding a domain touches main.py, the import-linter contract, next.config.ts's rewrites and
the Terraform invoker bindings. Missing any one of them fails silently in a different way
(no deploy, unchecked boundaries, a frontend 404, a 403 from Cloud Run) — so this test
reads all four from source and demands they agree with src/.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from shared.core.collections import CONTENT_COLLECTIONS

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _domain_packages() -> set[str]:
    return {p.parent.name for p in (BACKEND / "src").glob("*/__init__.py")}


def _http_functions_in_main() -> set[str]:
    return set(re.findall(r'_wanted\("(api_\w+)"\)', _read(BACKEND / "main.py")))


def test_every_domain_package_deploys_exactly_one_http_function() -> None:
    assert {name.removeprefix("api_") for name in _http_functions_in_main()} == (_domain_packages())


def test_import_linter_independence_covers_every_domain() -> None:
    config = tomllib.loads(_read(BACKEND / "pyproject.toml"))
    contracts = config["tool"]["importlinter"]["contracts"]
    independence = next(c for c in contracts if c["type"] == "independence")
    assert {m.removeprefix("src.") for m in independence["modules"]} == _domain_packages()


def test_next_config_rewrites_every_http_function() -> None:
    source = _read(REPO / "frontend" / "next.config.ts")
    block = re.search(r"const DOMAINS = \[(.*?)\]", source, re.DOTALL)
    assert block, "DOMAINS array not found in next.config.ts"
    rewritten = set(re.findall(r'"(\w+)"', block.group(1)))
    assert {f"api_{d}" for d in rewritten} == _http_functions_in_main()


def test_terraform_grants_invoker_on_every_http_function() -> None:
    source = _read(REPO / "infra" / "terraform" / "modules" / "functions" / "main.tf")
    block = re.search(r'variable "http_functions" \{.*?default = \[(.*?)\]', source, re.DOTALL)
    assert block, "http_functions default not found"
    assert set(re.findall(r'"(api_\w+)"', block.group(1))) == _http_functions_in_main()


def test_content_collections_match_the_publicly_readable_schemas() -> None:
    public = set()
    for path in (REPO / "architecture" / "schemas").glob("*.schema.json"):
        meta = json.loads(_read(path)).get("x-firestore", {})
        if meta.get("publicRead") is True:
            public.add(meta["collection"])
    assert set(CONTENT_COLLECTIONS) == public
