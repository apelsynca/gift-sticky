import random

import structlog
from gchanges import GiftChanges

from sticky.bot import create_bot
from sticky.gift_floor.service import gift_floor as gift_floor_service
from sticky.kit.database.postgres import create_async_sessionmaker
from sticky.logging import Logger
from sticky.postgres import create_async_engine
from sticky.sticker_pack import (
    ensure_sticker_pack_is_created,
    update_sticker_pack_in_telegram,
)
from sticky.sticker_renderer import GENERATIONS_PATH
from sticky.sticker_renderer import renderer as sticker_renderer
from sticky.sticker_renderer.types import StickerPayload
from sticky.thermos_proxy.client import ThermosProxy

log: Logger = structlog.get_logger()


async def sticky_job_runner() -> None:
    bot = create_bot()

    async_engine = create_async_engine("app")
    async_sessionmaker = create_async_sessionmaker(async_engine)

    thermos_proxy = ThermosProxy()

    async with async_sessionmaker() as session:
        await ensure_sticker_pack_is_created(session, bot)
        await gift_floor_service.update_from_thermos(session, thermos_proxy)
        await generate_stickers()
        await update_sticker_pack_in_telegram(bot)


async def generate_stickers() -> None:
    gift_changes = GiftChanges()
    gifts = await gift_changes.get_names()

    for gift_name, gift_id in gifts.items():
        payload = await get_payload_for_gift_collection(gift_name, gift_id)
        await sticker_renderer.render_and_save_to_file(
            payload=payload, path=f"{GENERATIONS_PATH}/{gift_name}.png"
        )


async def get_payload_for_gift_collection(name: str, gift_id: str) -> StickerPayload:
    floor_price = 0
    log.debug("Generating sticker for collection", name=name, floor_price=floor_price)

    return StickerPayload(
        gift_id=gift_id,
        price=floor_price,
        usd_price=floor_price * 1.4,
        stars_price=round(floor_price * 1.4 / 0.015),
        percent=(random.randint(0, 100) - 50) / 100,
    )
