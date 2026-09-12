"""A thread-free ASGI-to-WSGI bridge, used instead of a2wsgi.ASGIMiddleware.

a2wsgi.ASGIMiddleware spins up a persistent background thread running its own event
loop at *construction* time, and dispatches each WSGI call to it across the thread
boundary. That is fine in a long-lived, never-forked process — but Werkzeug's
development server reloader (which functions-framework uses locally) and Cloud
Functions' own worker-pool model both fork. `os.fork()` only duplicates the calling
thread; a background thread that existed in the parent simply does not exist in the
child, and Python emits its own warning to this effect
("this process is multi-threaded, use of fork() may lead to deadlocks in the child").
Waiting on that thread from the child — which is exactly what a2wsgi's
`asyncio.run_coroutine_threadsafe(coro, self.loop).result()` does — hangs forever, since
nothing will ever run `self.loop` again. This was reproduced directly: an isolated
`os.fork()` test against a constructed `ASGIMiddleware` hung the child on every attempt.

The fix here has no persistent thread at all: every WSGI call gets a fresh event loop via
`asyncio.run()`, used once and discarded. That is strictly less efficient per call than a
warm, reused loop — irrelevant for a Cloud Function, which cold-starts fresh per instance
and handles one request at a time regardless. `build_scope` is imported from a2wsgi
because it is a small, pure, stateless WSGI-environ-to-ASGI-scope converter with no
threading of its own; only a2wsgi's *classes* create the background thread.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from a2wsgi.wsgi_typing import Environ

from a2wsgi.asgi import build_scope

WSGIApp = Callable[[dict[str, Any], Callable[..., Any]], Iterable[bytes]]


def wsgi_from_asgi(app: Callable[..., Any]) -> WSGIApp:
    """Wrap an ASGI app (e.g. a FastAPI instance) as a plain WSGI callable.

    The outward-facing signature takes a plain dict, matching what callers like
    ``werkzeug.Response.from_app`` expect — ``build_scope`` wants a2wsgi's own narrower
    ``Environ`` TypedDict, so the cast is purely to satisfy that structural mismatch
    between the two libraries' stubs, not a real type difference at runtime.
    """

    def wsgi_app(environ: dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        scope = build_scope(cast("Environ", environ))

        body_stream = environ.get("wsgi.input")
        content_length = int(environ.get("CONTENT_LENGTH") or 0)
        request_body = body_stream.read(content_length) if body_stream and content_length else b""

        response: dict[str, Any] = {"status": 500, "headers": [], "body": bytearray()}
        request_sent = False

        async def receive() -> dict[str, Any]:
            nonlocal request_sent
            if request_sent:
                return {"type": "http.disconnect"}
            request_sent = True
            return {"type": "http.request", "body": request_body, "more_body": False}

        async def send(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                response["status"] = message["status"]
                response["headers"] = message.get("headers", [])
            elif message["type"] == "http.response.body":
                response["body"].extend(message.get("body", b""))

        asyncio.run(app(scope, receive, send))

        status_line = f"{response['status']} {HTTPStatus(response['status']).phrase}"
        headers = [(k.decode("latin1"), v.decode("latin1")) for k, v in response["headers"]]
        start_response(status_line, headers)
        return [bytes(response["body"])]

    return wsgi_app
