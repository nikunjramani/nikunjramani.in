"""make_app() — the FastAPI application every router runs in, built once.

apps/api.py builds the deployed service from it; tests build one per router. Three things
are load-bearing:

1. **Every error has one JSON shape**, `{"error": {code, message}}`, the one the admin client
   parses: a service's DomainError, a request body FastAPI rejects, a path nothing serves,
   and an unhandled exception alike.
2. `/docs` and `/openapi.json` exist only outside production — in production they leak the
   whole admin surface.
3. **Trailing slashes never redirect.** A collection root is declared as `"/"`, so it lives at
   `/api/v1/content/skills/`, but the browser reaches it through the Next.js rewrite, which
   drops the slash. Starlette's default answer is a 307 to the slashed URL — on the Cloud Run
   host, not the site's, so the browser would leave the site and lose its Authorization
   header. Instead, a request that matches no route as sent is retried with a slash added.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import AbstractAsyncContextManager

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.routing import Match
from starlette.types import ASGIApp, Receive, Scope, Send

from kernel.config import get_settings
from kernel.errors import DomainError
from kernel.logging import configure_logging, get_logger, trace_id

log = get_logger(__name__)


#: Codes for the statuses Starlette raises itself (a path or method nothing serves).
_HTTP_CODES = {404: "not_found", 405: "method_not_allowed"}


def error_response(
    status_code: int, code: str, message: str, headers: Mapping[str, str] | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
        headers=headers,
    )


Lifespan = Callable[[FastAPI], AbstractAsyncContextManager[None]]


def make_app(router: APIRouter, name: str, *, lifespan: Lifespan | None = None) -> FastAPI:
    """Build the FastAPI app around `router`."""
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title=f"nikunjramani.in · {name}",
        docs_url=None if settings.is_production else "/docs",
        openapi_url=None if settings.is_production else "/openapi.json",
        redirect_slashes=False,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.add_middleware(TrailingSlashFallback, router=app.router)
    app.add_middleware(TraceContext)

    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        log.warning("domain error", extra={"extra_fields": {"code": exc.code}})
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        # The first problem, phrased like CrudService._validate's: "<field.path>: <reason>".
        errors = exc.errors()
        first = errors[0] if errors else {}
        where = ".".join(str(p) for p in first.get("loc", ()) if p != "body") or "body"
        return error_response(422, "validation_error", f"{where}: {first.get('msg', 'invalid')}")

    @app.exception_handler(HTTPException)
    async def _http_error(_: Request, exc: HTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, "http_error")
        return error_response(exc.status_code, code, str(exc.detail), exc.headers)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # Starlette still logs the traceback and re-raises; this only shapes the response.
        return error_response(500, "internal_error", "Something went wrong.")

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


class TraceContext:
    """Binds Cloud Run's trace id (X-Cloud-Trace-Context: `<trace>/<span>;o=1`) to the
    request, so every log line it writes is grouped under it (kernel/logging.py)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        header = dict(scope["headers"]).get(b"x-cloud-trace-context", b"").decode("latin-1")
        token = trace_id.set(header.split("/", 1)[0])
        try:
            await self.app(scope, receive, send)
        finally:
            trace_id.reset(token)
