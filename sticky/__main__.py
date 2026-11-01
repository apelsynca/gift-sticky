import argparse
import asyncio

import structlog

from sticky.bot import create_bot
from sticky.kit.database.postgres import create_async_sessionmaker
from sticky.logging import Logger
from sticky.logging import configure as configure_logging
from sticky.postgres import create_async_engine
from sticky.sticker.utils import render_stickers
from sticky.sticker_pack.tasks import update_sticker_pack
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
    async_engine = create_async_engine("script")
    async_sessionmaker = create_async_sessionmaker(async_engine)

    try:
        async with async_sessionmaker() as session:
            await render_stickers(session)
    finally:
        await async_engine.dispose()


async def sticky_generate_and_post_once() -> None:
    thermos_proxy = ThermosProxy()

    async_engine = create_async_engine("app")
    async_sessionmaker = create_async_sessionmaker(async_engine)

    try:
        async with create_bot() as bot, async_sessionmaker() as session:
            await update_sticker_pack(
                session=session, bot=bot, thermos_proxy=thermos_proxy
            )
    finally:
        await async_engine.dispose()


async def run() -> None:
    args = parser.parse_args()

    if args.generate:
        await render_stickers_once()
    else:
        await sticky_generate_and_post_once()


def main() -> None:
    configure_logging()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        log.debug("Bye!")


if __name__ == "__main__":
    main()
