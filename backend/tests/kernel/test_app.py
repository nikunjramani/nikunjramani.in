"""make_app's wiring (kernel/app.py).

Trailing slashes: a collection root is declared at `/` but reached through the Next.js
rewrite without the slash, and must never be answered with a redirect — the redirect would
point at the Cloud Run host, not the site. Errors: every one has the admin client's shape."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel

from kernel.app import make_app
from kernel.logging import trace_id

items = APIRouter()


@items.get("/")
async def list_items() -> list[str]:
    return ["a"]


@items.get("/public")
async def public_items() -> list[str]:
    return ["p"]


def _client() -> TestClient:
    root = APIRouter()
    root.include_router(items, prefix="/api/v1/content/items")
    return TestClient(make_app(root, "app-test"), follow_redirects=False)


def test_collection_root_answers_without_the_slash() -> None:
    response = _client().get("/api/v1/content/items")
    assert response.status_code == 200
    assert response.json() == ["a"]


def test_collection_root_answers_with_the_slash() -> None:
    assert _client().get("/api/v1/content/items/").json() == ["a"]


def test_a_route_declared_without_a_slash_is_untouched() -> None:
    assert _client().get("/api/v1/content/items/public").json() == ["p"]


def test_an_unknown_path_is_a_plain_404_not_a_redirect() -> None:
    assert _client().get("/api/v1/content/nothing").status_code == 404


def test_wrong_method_is_405_after_the_fallback() -> None:
    assert _client().delete("/api/v1/content/items").status_code == 405


# ── one error shape (kernel/app.py, point 1) ────────────────────────────────

errors = APIRouter()


class Body(BaseModel):
    name: str


@errors.post("/echo")
def echo(body: Body) -> Body:
    return body


@errors.get("/boom")
def boom() -> None:
    raise RuntimeError("unexpected")


@errors.get("/traced")
def traced() -> dict[str, str]:
    return {"trace": trace_id.get()}


def _errors_client() -> TestClient:
    return TestClient(make_app(errors, "errors-test"), raise_server_exceptions=False)


def test_a_rejected_body_has_the_domain_error_shape() -> None:
    response = _errors_client().post("/echo", json={})
    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "validation_error", "message": "name: Field required"}
    }


def test_an_unknown_path_has_the_domain_error_shape() -> None:
    response = _errors_client().get("/nowhere")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_a_wrong_method_has_the_domain_error_shape() -> None:
    response = _errors_client().delete("/echo")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_an_unhandled_exception_is_a_500_without_details() -> None:
    response = _errors_client().get("/boom")
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Something went wrong."}
    }


def test_the_cloud_run_trace_id_is_bound_to_the_request() -> None:
    response = _errors_client().get(
        "/traced", headers={"X-Cloud-Trace-Context": "105445aa7843bc8bf206b12000100000/1;o=1"}
    )
    assert response.json() == {"trace": "105445aa7843bc8bf206b12000100000"}
    assert trace_id.get() == ""  # reset once the request is done
