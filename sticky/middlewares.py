from litestar.types import ASGIApp, Receive, Scope, Send


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
