import os

import structlog

from sticky.converter import ton_converter
from sticky.exceptions import ResourceNotFound, StickyError
from sticky.gift.service import gift as gift_service
from sticky.gift_floor.service import gift_floor as gift_floor_service
from sticky.logging import Logger
from sticky.models import Gift
from sticky.postgres import AsyncSession
from sticky.sticker_renderer import renderer as sticker_renderer
from sticky.sticker_renderer.types import StickerPayload

log: Logger = structlog.get_logger()


async def render_stickers(session: AsyncSession, *, skip_existing: bool = False) -> None:
    """
    Iterates over all gifts that exist in db,
    gets a payload for that and renders them
    """
    gifts = await gift_service.get_all(session)

    for gift in gifts:
        if (
            os.path.exists(sticker_renderer.get_render_path(gift.telegram_id))
            and skip_existing
        ):
            log.debug(
                "Skipping sticker render, since already exists",
                skip_existing=skip_existing,
            )
            continue

        try:
            payload = await get_sticker_payload_for_gift_collection(session, gift=gift)
        except ResourceNotFound as exc:
            log.warning(
                "Skipping rendering gift, since getting payload raised not found",
                exc_info=exc,
            )
            continue
        except StickyError as exc:
            log.warning(
                "Skipping rendering gift, since getting payload raised", exc_info=exc
            )
            continue

        await sticker_renderer.render_and_save_to_file(
            payload=payload, path=sticker_renderer.get_render_path(gift.telegram_id)
        )


async def get_sticker_payload_for_gift_collection(
    session: AsyncSession, gift: Gift
) -> StickerPayload:
    """
    Gets a gift floor price, floor price change by gift

    Returns `StickerPayload` - all the required data to generate a sticker
    """

    gift_floor = await gift_floor_service.get_latest(session, gift=gift)
    ton_floor_price = gift_floor.floor

    async with ton_converter() as converter:
        floor_change = await gift_floor_service.get_floor_change(session, gift=gift)
        floor_change = round(floor_change, 2)

        log.debug(
            "Got payload for sticker render", name=gift.name, floor_price=ton_floor_price
        )

        return StickerPayload(
            gift_id=gift.telegram_id,
            price=ton_floor_price,
            usd_price=converter.to_usd(ton=ton_floor_price),
            stars_price=converter.to_stars(ton=ton_floor_price),
            percent=floor_change,
        )
