import argparse
import asyncio

import structlog

from sticky.bot import create_bot
from sticky.gift_floor.service import gift_floor as gift_floor_service
from sticky.helpers import render_stickers
from sticky.kit.database.postgres import create_async_sessionmaker
from sticky.logging import Logger
from sticky.postgres import create_async_engine
from sticky.sticker_pack import (
    ensure_sticker_pack_is_created,
    update_sticker_pack_in_telegram,
)
from sticky.thermos_proxy.client import ThermosProxy

parser = argparse.ArgumentParser(
    description="Sticky - telegram gift's prices/price-changes sticker pack"
)

parser.add_argument(
    "--generate",
    help="Just generate the sticker pack and exit",
    default=False,
    required=False,
    action="store_true",
)

log: Logger = structlog.get_logger()


async def render_stickers_once() -> None:
    async_engine = create_async_engine("app")
    async_sessionmaker = create_async_sessionmaker(async_engine)

    async with async_sessionmaker() as session:
        await render_stickers(session)


async def sticky_job_runner() -> None:
    bot = create_bot()

    async_engine = create_async_engine("app")
    async_sessionmaker = create_async_sessionmaker(async_engine)

    thermos_proxy = ThermosProxy()

    async with async_sessionmaker() as session:
        await ensure_sticker_pack_is_created(session, bot)
        await gift_floor_service.update_from_thermos(session, thermos_proxy)
        await render_stickers(session, skip_existing=True)
        await update_sticker_pack_in_telegram(session, bot)


async def run() -> None:
    args = parser.parse_args()

    if args.generate:
        await render_stickers_once()
    else:
        await sticky_job_runner()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        log.debug("Bye!")


if __name__ == "__main__":
    main()
