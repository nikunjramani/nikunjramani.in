"""main.py, actually imported — not just read.

Deploy discovery only ever sees what main.py exposes, and a decorator like
storage_fn.on_object_finalized raises at import time if misconfigured. Neither shows up in a
unit test that imports one subdomain; both show up here.
"""

from __future__ import annotations

import ast
import importlib
import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_every_listed_function_is_importable(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("FUNCTION_TARGET", raising=False)
    import main

    importlib.reload(main)
    assert main.__all__, "main.py exports nothing — that can't be right"
    for name in main.__all__:
        assert hasattr(main, name), f"{name} is listed but was never imported"


def test_every_function_defined_in_a_subdomain_main_is_listed() -> None:
    """A Firebase function defined in some src/<domain>/<sub>/main.py but missing from its
    domain's FUNCTIONS table would exist in the repo and silently never deploy."""
    import main

    defined: dict[str, str] = {}
    for path in (BACKEND_ROOT / "src").glob("*/*/main.py"):
        module = ".".join(path.relative_to(BACKEND_ROOT).with_suffix("").parts)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.decorator_list:
                defined[node.name] = module
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                call = node.value.func
                if isinstance(call, ast.Name) and call.id == "make_function":
                    defined[node.targets[0].id] = module  # type: ignore[attr-defined]

    assert defined == main.FUNCTIONS


def test_function_target_imports_exactly_one_subdomain() -> None:
    """A real container imports main.py once, in a fresh interpreter, with FUNCTION_TARGET
    already set — importlib.reload can't model that, a subprocess can."""
    code = (
        "import sys, main; "
        "print(hasattr(main, 'api_ops_health')); "
        "print(hasattr(main, 'api_inbox_contact')); "
        "print(sorted(m for m in sys.modules if m.count('.') == 3 and m.endswith('.main')))"
    )
    env = {**os.environ, "FUNCTION_TARGET": "api_ops_health"}
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    has_health, has_contact, loaded = result.stdout.splitlines()
    assert (has_health, has_contact) == ("True", "False")
    assert loaded == "['src.ops.health.main']"  # the one subdomain, nothing else


def test_production_manifest_has_identity_secrets_and_limits() -> None:
    """Inspect fresh deploy discovery, where missing options silently ship bad config."""
    code = """
import main
expected_secrets = {
    'on_contact_created': {'CONTACT_EMAIL_TO', 'RESEND_API_KEY'},
}
two_instances = {'api_media_upload', 'api_media_library', 'on_media_uploaded'}
for name in main.__all__:
    endpoint = getattr(main, name).__firebase_endpoint__
    assert endpoint.serviceAccountEmail == (
        'functions-runtime@nikunjramani-in.iam.gserviceaccount.com'
    ), name
    assert endpoint.maxInstances == (2 if name in two_instances else 3), name
    bound = {s['key'] for s in endpoint.secretEnvironmentVariables or []}
    assert bound == expected_secrets.get(name, set()), (name, bound)
"""
    env = {k: v for k, v in os.environ.items() if k != "FUNCTION_TARGET"}
    subprocess.run([sys.executable, "-c", code], cwd=BACKEND_ROOT, env=env, check=True)
