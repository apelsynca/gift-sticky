import random

import structlog
from gchanges import GiftChanges

from sticky.logging import Logger
from sticky.sticker_generator import GENERATIONS_PATH
from sticky.sticker_generator import generator as sticker_generator
from sticky.sticker_generator.types import StickerPayload
from sticky.thermos_proxy.client import ThermosProxy

log: Logger = structlog.get_logger()


async def get_payload_for_gift_collection(
    thermos_proxy: ThermosProxy, name: str, gift_id: str
) -> StickerPayload:
    collection_data = await thermos_proxy.get_collection(collection_name=name)
    log.debug(
        "Generating sticker for collection",
        name=name,
        floor_price=collection_data.collection.stats.floor,
    )

    floor_price = collection_data.collection.stats.floor

    return StickerPayload(
        gift_id=gift_id,
        price=floor_price,
        usd_price=floor_price * 1.4,
        stars_price=round(floor_price * 1.4 / 0.015),
        percent=(random.randint(0, 100) - 50) / 100,
    )


async def sticky_job_runner() -> None:
    await generate_stickers()


async def generate_stickers() -> None:
    thermos_proxy = ThermosProxy()
    gift_changes = GiftChanges()
    gifts = await gift_changes.get_names()

    for gift_name, gift_id in gifts.items():
        payload = await get_payload_for_gift_collection(thermos_proxy, gift_name, gift_id)
        await sticker_generator.generate_to_file(
            payload=payload, path=f"{GENERATIONS_PATH}/{gift_name}.png"
        )
