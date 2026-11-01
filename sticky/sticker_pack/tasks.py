import structlog
from aiogram import Bot
from litestar_queues import task

from sticky.bot import create_bot
from sticky.gift_floor.service import gift_floor as gift_floor_service
from sticky.logging import Logger
from sticky.postgres import AsyncSession, WorkerSessionMaker
from sticky.sticker.utils import render_stickers
from sticky.sticker_pack.utils import (
    ensure_sticker_pack_is_created,
    update_sticker_pack_in_telegram,
)
from sticky.thermos_proxy.client import ThermosProxy

log: Logger = structlog.get_logger()

UPDATE_TIMEOUT_SECONDS = 30 * 60  # well under the hourly schedule


@task(
    "sticker_pack.update",
    cron="@hourly",
    timezone="UTC",
    timeout=UPDATE_TIMEOUT_SECONDS,
)
async def update_sticker_pack_task() -> None:
    thermos_proxy = ThermosProxy()

    async with create_bot() as bot, WorkerSessionMaker() as session:
        await update_sticker_pack(session=session, bot=bot, thermos_proxy=thermos_proxy)


async def update_sticker_pack(
    session: AsyncSession, bot: Bot, thermos_proxy: ThermosProxy
) -> None:
    """Basically main method where update task execution is"""
    await ensure_sticker_pack_is_created(session, bot)
    await session.commit()

    await gift_floor_service.update_from_thermos(session, thermos_proxy)
    await session.commit()

    await render_stickers(session)

    await update_sticker_pack_in_telegram(session, bot)
    await session.commit()
