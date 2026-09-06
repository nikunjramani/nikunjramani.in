"""make_function() — the FastAPI-to-Firebase adapter, written once.

Every domain calls this to export exactly one deployed function. See ADR 0011.

Two non-obvious details are load-bearing here:

1. The Firebase SDK derives the *deployed* function name from the handler's ``__name__``,
   read at decoration time. So ``__name__`` is set before ``on_request`` is applied —
   otherwise every domain would deploy as "handler" and collide.
2. ``Response.from_app`` runs a WSGI app against the incoming request environ and returns a
   real Response. That is the bridge from Firebase's Flask-shaped handler to FastAPI's ASGI.
3. ``https_fn.Request``/``Response`` are re-exports of Flask's, but are not declared as public
   exports, so they are imported from Flask directly to keep ``mypy --strict`` happy.
"""

from typing import Any, cast

from a2wsgi import ASGIMiddleware
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from firebase_functions import https_fn, options
from flask import Request as FlaskRequest
from flask import Response as FlaskResponse

from shared.core.config import get_settings
from shared.core.errors import DomainError
from shared.core.logging import configure_logging, get_logger

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
    # Both casts are structural, not semantic: FastAPI *is* an ASGI app and ASGIMiddleware
    # *is* a WSGI app, but neither library's protocol types line up under --strict.
    wsgi = cast("Any", ASGIMiddleware(cast("Any", make_app(router, name))))

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
