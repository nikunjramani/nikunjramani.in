"""make_function() — the FastAPI-to-Firebase adapter, written once.

Every domain calls this to export exactly one deployed function. See ADR 0011.

Three non-obvious details are load-bearing here:

1. The Firebase SDK derives the *deployed* function name from the handler's ``__name__``,
   read at decoration time. So ``__name__`` is set before ``on_request`` is applied —
   otherwise every domain would deploy as "handler" and collide.
2. ``https_fn.Request``/``Response`` are re-exports of Flask's, but are not declared as public
   exports, so they are imported from Flask directly to keep ``mypy --strict`` happy.
3. The WSGI bridge is `shared.wsgi_bridge`, not `a2wsgi.ASGIMiddleware` directly.
   `ASGIMiddleware` spins up a persistent background thread at construction time, and a
   forked child process — which is exactly what Werkzeug's dev-server reloader and Cloud
   Functions' own worker model both do — inherits a dead copy of that thread. Waiting on
   it then hangs forever, reproduced directly with `os.fork()` in development. See
   `shared/wsgi_bridge.py` for the full account and the fix (a fresh `asyncio.run()` per
   call, no persistent thread to survive a fork).
"""

from typing import Any, cast

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from firebase_functions import https_fn, options
from flask import Request as FlaskRequest
from flask import Response as FlaskResponse

from shared.core.config import get_settings
from shared.core.errors import DomainError
from shared.core.logging import configure_logging, get_logger
from shared.wsgi_bridge import wsgi_from_asgi

log = get_logger(__name__)

# Mumbai — closest region to the author, and Firestore lives in the same place.
DEFAULT_REGION = "asia-south1"


def make_app(router: APIRouter, name: str) -> FastAPI:
    """Build the FastAPI app for one domain."""
    settings = get_settings()
    configure_logging()

    # /docs is a development affordance. In production it is an information leak.
    app = FastAPI(
        title=f"nikunjramani.in · {name}",
        docs_url=None if settings.is_production else "/docs",
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        log.warning("domain error", extra={"extra_fields": {"code": exc.code}})
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    app.include_router(router)
    return app


def make_function(
    router: APIRouter,
    name: str,
    *,
    memory: options.MemoryOption = options.MemoryOption.MB_256,
    max_instances: int = 3,
    region: str = DEFAULT_REGION,
) -> Any:
    """Wrap a FastAPI router as one deployed Firebase HTTP function named ``name``."""
    wsgi = wsgi_from_asgi(make_app(router, name))

    def _handler(req: FlaskRequest) -> FlaskResponse:
        # from_app is inherited from werkzeug, whose stub under-reports the return type;
        # at runtime it constructs cls, so this really is a flask Response.
        return cast("FlaskResponse", FlaskResponse.from_app(wsgi, req.environ))

    # Must happen before decoration — see the module docstring.
    _handler.__name__ = name
    _handler.__qualname__ = name

    decorate = https_fn.on_request(
        memory=memory,
        max_instances=max_instances,
        region=region,
    )
    return decorate(_handler)
