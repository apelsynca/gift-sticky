import structlog
from litestar.middleware.base import MiddlewareProtocol
from litestar.types import ASGIApp, Receive, Scope, Send

from sticky.logging import TraceID


def proxy_headers_middleware(app: ASGIApp) -> ASGIApp:
    """Middleware to trust Traefik's X-Forwarded-Proto header."""

    async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))

            # If Traefik forwarded the request as HTTPS, update the ASGI scope
            if headers.get(b"x-forwarded-proto") == b"https":
                scope["scheme"] = "https"

        await app(scope, receive, send)

    return middleware


class LogTraceIdMiddleware(MiddlewareProtocol):
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        trace_id = TraceID.set()

        structlog.contextvars.bind_contextvars(
            trace_id=trace_id,
            method=scope["method"],
            path=scope["path"],
        )

        try:
            await self.app(scope, receive, send)
        finally:
            structlog.contextvars.unbind_contextvars("trace_id", "method", "path")
            TraceID.clear()
