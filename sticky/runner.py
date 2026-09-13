import structlog

from sticky.bot import create_bot
from sticky.gift.service import gift as gift_service
from sticky.gift_floor.service import gift_floor as gift_floor_service
from sticky.kit.database.postgres import create_async_sessionmaker
from sticky.logging import Logger
from sticky.models import Gift
from sticky.postgres import AsyncSession, create_async_engine
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
        await generate_stickers(session)
        await update_sticker_pack_in_telegram(session, bot)


async def generate_stickers(session: AsyncSession) -> None:
    gifts = await gift_service.get_all(session)

    for gift in gifts:
        payload = await get_payload_for_gift_collection(session, gift=gift)
        await sticker_renderer.render_and_save_to_file(
            payload=payload, path=f"{GENERATIONS_PATH}/{gift.telegram_id}.png"
        )


async def get_payload_for_gift_collection(
    session: AsyncSession, gift: Gift
) -> StickerPayload:
    floor_change = await gift_floor_service.get_floor_change(session, gift=gift)
    gift_floor = await gift_floor_service.get_latest(session, gift=gift)

    floor_price = gift_floor.floor
    usd_price = floor_price * 1.4
    stars_price = round(floor_price * 1.4 / 0.015)

    log.debug(
        "Generating sticker for collection", name=gift.name, floor_price=floor_price
    )

    return StickerPayload(
        gift_id=gift.telegram_id,
        price=floor_price,
        usd_price=usd_price,
        stars_price=stars_price,
        percent=floor_change,
    )
