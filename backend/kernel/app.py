"""make_app() — the FastAPI application every router runs in, built once.

apps/api.py builds the deployed service from it; tests build one per router. Three things
are load-bearing:

1. Domain errors become the JSON shape the admin client parses (`{"error": {code, message}}`).
2. `/docs` and `/openapi.json` exist only outside production — in production they leak the
   whole admin surface.
3. **Trailing slashes never redirect.** A collection root is declared as `"/"`, so it lives at
   `/api/v1/content/skills/`, but the browser reaches it through the Next.js rewrite, which
   drops the slash. Starlette's default answer is a 307 to the slashed URL — on the Cloud Run
   host, not the site's, so the browser would leave the site and lose its Authorization
   header. Instead, a request that matches no route as sent is retried with a slash added.
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.routing import Match
from starlette.types import ASGIApp, Receive, Scope, Send

from kernel.config import get_settings
from kernel.errors import DomainError
from kernel.logging import configure_logging, get_logger

log = get_logger(__name__)


def make_app(router: APIRouter, name: str) -> FastAPI:
    """Build the FastAPI app around `router`."""
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title=f"nikunjramani.in · {name}",
        docs_url=None if settings.is_production else "/docs",
        openapi_url=None if settings.is_production else "/openapi.json",
        redirect_slashes=False,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.add_middleware(TrailingSlashFallback, router=app.router)

    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        log.warning("domain error", extra={"extra_fields": {"code": exc.code}})
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    app.include_router(router)
    return app


class TrailingSlashFallback:
    """Serves `/x` from the route declared at `/x/` when nothing is declared at `/x` — the
    request is rewritten in place, never redirected (see the module docstring)."""

    def __init__(self, app: ASGIApp, router: APIRouter) -> None:
        self.app = app
        self.router = router

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and not scope["path"].endswith("/") and not self._matches(scope):
            slashed = {
                **scope,
                "path": scope["path"] + "/",
                "raw_path": scope.get("raw_path", scope["path"].encode()) + b"/",
            }
            if self._matches(slashed):
                scope = slashed
        await self.app(scope, receive, send)

    def _matches(self, scope: Scope) -> bool:
        # PARTIAL is a path match with the wrong method: still the right route (405, not 404).
        return any(route.matches(scope)[0] != Match.NONE for route in self.router.routes)
