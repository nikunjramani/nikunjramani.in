"""main.py, actually imported — not just read.

This is the one test in the whole suite that would have caught two real bugs on its own:
on_contact_created and on_media_uploaded existed as working code but were never imported
into main.py at all, so functions_framework's discovery (which only ever sees what main.py
actually imports) would never have found them — they would have silently never deployed.
Separately, storage_fn.on_object_finalized raises at *decoration* time if its bucket isn't
resolvable, which only ever surfaces by actually running the import, not by reading the
code. Every other test in this suite imports domains piecemeal and would have missed both.
"""

from __future__ import annotations

import ast
import importlib
import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_every_exported_name_is_actually_importable(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("FUNCTION_TARGET", raising=False)
    import main

    importlib.reload(main)
    assert main.__all__, "main.py exports nothing — that can't be right"
    for name in main.__all__:
        assert hasattr(main, name), f"{name} is in __all__ but was never actually imported"


def test_every_trigger_and_scheduled_module_is_reachable_from_main() -> None:
    """Every src/<domain>/triggers.py or scheduled.py that defines a function must have a
    corresponding line in main.py — otherwise it exists in the repo but never deploys."""
    backend_root = BACKEND_ROOT
    main_source = (backend_root / "main.py").read_text(encoding="utf-8")

    trigger_files = list((backend_root / "src").glob("*/triggers.py")) + list(
        (backend_root / "src").glob("*/scheduled.py")
    )
    missing: list[str] = []
    for path in trigger_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            has_decorator = any(isinstance(d, ast.Call) for d in node.decorator_list)
            if has_decorator and f"import {node.name}" not in main_source:
                missing.append(f"{path.relative_to(backend_root)}::{node.name}")

    assert not missing, f"Defined but never imported in main.py: {missing}"


def test_function_target_narrows_to_exactly_one_domain() -> None:
    """The whole point of the FUNCTION_TARGET conditional (ADR 0011) — setting it must
    import only the matching function, not every domain's FastAPI app.

    A real deployed container never reloads main.py with a changing FUNCTION_TARGET — it
    does exactly one import, in a fresh interpreter, with the variable already set before
    that import starts. importlib.reload() does not model that: it re-executes the module
    over the *same* namespace, and a name bound by an earlier execution survives even once
    the branch that set it stops firing, since reload never clears old attributes first.
    A real subprocess is what actually reproduces the one thing this test needs to prove.
    """
    env = {**os.environ, "FUNCTION_TARGET": "api_system"}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import main; print('api_system' in dir(main)); "
            "print('api_contact' in dir(main)); print('on_media_uploaded' in dir(main))",
        ],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    has_system, has_contact, has_media_trigger = result.stdout.strip().splitlines()
    assert has_system == "True"
    assert has_contact == "False"
    assert has_media_trigger == "False"


def test_production_manifest_has_runtime_identity_secrets_and_limits() -> None:
    """Inspect fresh deploy discovery, where missing options silently ship bad config."""
    code = """
import main
for name in main.__all__:
    endpoint = getattr(main, name).__firebase_endpoint__
    expected_sa = 'functions-runtime@nikunjramani-in.iam.gserviceaccount.com'
    assert endpoint.serviceAccountEmail == expected_sa, name
    assert endpoint.maxInstances == (2 if name in {'api_media', 'on_media_uploaded'} else 3), name
def secret_keys(name):
    bound = getattr(main, name).__firebase_endpoint__.secretEnvironmentVariables or []
    return {s['key'] for s in bound}
expected = {
    'api_contact': {'TURNSTILE_SECRET_KEY'},
    'on_contact_created': {'CONTACT_EMAIL_TO', 'RESEND_API_KEY'},
}
for name in main.__all__:
    assert secret_keys(name) == expected.get(name, set()), (name, secret_keys(name))
"""
    env = {k: v for k, v in os.environ.items() if k != "FUNCTION_TARGET"}
    subprocess.run([sys.executable, "-c", code], cwd=BACKEND_ROOT, env=env, check=True)
