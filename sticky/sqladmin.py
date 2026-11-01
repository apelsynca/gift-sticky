import hashlib
import hmac
from collections.abc import Sequence
from typing import ClassVar

import structlog
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from sqladmin_litestar_plugin import SQLAdminPlugin
from starlette.requests import Request

from sticky.admin_auth import verify_admin_credentials
from sticky.config import settings
from sticky.logging import Logger
from sticky.models import Gift, GiftFloor, Sticker
from sticky.postgres import create_async_engine

log: Logger = structlog.get_logger()


def _get_session_token() -> str:
    """
    Session cookies are only signed, so the credentials can't be stored in them.
    Derived from the credentials, so changing them invalidates existing sessions.
    """
    credentials = f"{settings.ADMIN_USERNAME}\0{settings.ADMIN_PASSWORD}".encode()
    return hmac.new(
        settings.ADMIN_AUTH_KEY.encode(), credentials, hashlib.sha256
    ).hexdigest()


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        # Session cookies are forgeable without the signing key
        if not settings.ADMIN_AUTH_KEY:
            log.warning("Admin login is disabled, since ADMIN_AUTH_KEY is not set")
            return False

        form = await request.form()
        username, password = form.get("username"), form.get("password")

        if (
            not isinstance(username, str)
            or not isinstance(password, str)
            or not verify_admin_credentials(username, password)
        ):
            log.warning("Login attempt with wrong credentials")
            return False

        request.session.update({"token": _get_session_token()})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        if not settings.ADMIN_AUTH_KEY or not settings.ADMIN_PASSWORD:
            return False

        token = request.session.get("token")
        if not isinstance(token, str):
            return False

        return hmac.compare_digest(token.encode(), _get_session_token().encode())


class StickerAdminView(ModelView, model=Sticker):
    can_create = True

    column_list: ClassVar = [Sticker.gift_id, Sticker.emojis]


class GiftAdminView(ModelView, model=Gift):
    can_create = True

    column_list: ClassVar = [Gift.name, Gift.telegram_id, Gift.ignore_as_sticker]
    column_default_sort: ClassVar = [(Gift.name, False)]
    column_searchable_list: ClassVar = [Gift.name]


class GiftFloorAdminView(ModelView, model=GiftFloor):
    can_create = False
    can_edit = False

    column_list: ClassVar = [GiftFloor.floor, GiftFloor.gift_id, GiftFloor.created_at]
    column_default_sort: ClassVar = [(GiftFloor.floor, True)]

    page_size = 50
    page_size_options: ClassVar[Sequence[int]] = [50, 100, 150, 200]


async_engine = create_async_engine("app")
sqladmin_plugin = SQLAdminPlugin(
    views=[GiftAdminView, StickerAdminView, GiftFloorAdminView],
    engine=async_engine,
    authentication_backend=AdminAuth(secret_key=settings.ADMIN_AUTH_KEY),
)
