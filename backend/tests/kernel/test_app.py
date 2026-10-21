"""make_app's trailing-slash handling: a collection root is declared at `/` but reached
through the Next.js rewrite without the slash, and must never be answered with a redirect —
the redirect would point at the Cloud Run host, not the site (kernel/app.py)."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.testclient import TestClient

from kernel.app import make_app

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
