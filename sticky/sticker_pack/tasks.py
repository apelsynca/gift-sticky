import structlog
from litestar_queues import task

from sticky.bot import create_bot
from sticky.gift_floor.service import gift_floor as gift_floor_service
from sticky.helpers import render_stickers
from sticky.logging import Logger
from sticky.postgres import WorkerSessionMaker
from sticky.sticker_pack import (
    ensure_sticker_pack_is_created,
    update_sticker_pack_in_telegram,
)
from sticky.thermos_proxy.client import ThermosProxy

log: Logger = structlog.get_logger()


@task("sticker_pack.update", cron="@hourly", timezone="UTC")
async def update_sticker_pack() -> None:
    thermos_proxy = ThermosProxy()
    bot = create_bot()

    async with WorkerSessionMaker() as session:
        await ensure_sticker_pack_is_created(session, bot)
        await session.commit()

        await gift_floor_service.update_from_thermos(session, thermos_proxy)
        await session.commit()

        await render_stickers(session)

        await update_sticker_pack_in_telegram(session, bot)
        # last is auto-committed
