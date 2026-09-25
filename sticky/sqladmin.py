import secrets
from collections.abc import Sequence
from typing import ClassVar

import structlog
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from sqladmin_litestar_plugin import SQLAdminPlugin
from starlette.requests import Request

from sticky.config import settings
from sticky.logging import Logger
from sticky.models import Gift, GiftFloor, Sticker
from sticky.postgres import create_async_engine

log: Logger = structlog.get_logger()


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        request.session.update({"token": f"{username}:{password}"})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False

        username, password = token.split(":")

        right_username = username == settings.ADMIN_USERNAME
        right_password = secrets.compare_digest(password, settings.ADMIN_PASSWORD)

        if not right_username or not right_password:
            log.warning(
                "Login attempt with wrong credentials",
                right_username=right_username,
                right_password=right_password,
            )
            return False

        return True


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
