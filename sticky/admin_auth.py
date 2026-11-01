import base64
import secrets

from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler

from sticky.config import settings


def verify_admin_credentials(username: str, password: str) -> bool:
    """Always False when no admin password is configured."""
    if not settings.ADMIN_PASSWORD:
        return False

    right_username = secrets.compare_digest(
        username.encode(), settings.ADMIN_USERNAME.encode()
    )
    right_password = secrets.compare_digest(
        password.encode(), settings.ADMIN_PASSWORD.encode()
    )

    return right_username and right_password


def require_admin(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    """Route guard checking HTTP Basic credentials against the admin credentials."""
    scheme, _sep, encoded = connection.headers.get("Authorization", "").partition(" ")

    if scheme.lower() == "basic":
        try:
            decoded = base64.b64decode(encoded, validate=True).decode()
        except ValueError:  # covers both malformed base64 and non UTF-8 bytes
            decoded = ""

        username, separator, password = decoded.partition(":")

        if separator and verify_admin_credentials(username, password):
            return

    raise NotAuthorizedException(headers={"WWW-Authenticate": "Basic"})
