import argparse
import asyncio
import random

import structlog
from gchanges import GiftChanges

from sticky.logging import Logger
from sticky.sticker_generator import StickerPayload
from sticky.sticker_generator import generator as sticker_generator
from sticky.thermos_proxy import ThermosProxy

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

GENERATIONS_PATH = "generations"


async def generate() -> None:
    gift_changes = GiftChanges()
    names = await gift_changes.get_names()

    await _run_generation_loop(names)


async def _run_generation_loop(names: dict[str, str]):
    thermos_proxy = ThermosProxy()
    sleep_for = 1.25

    for name, gift_id in names.items():
        await asyncio.sleep(0.03)
        collection_data = await thermos_proxy.get_collection(collection_name=name)
        log.debug(
            "Generating sticker for collection",
            name=name,
            floor_price=collection_data.collection.stats.floor,
        )

        floor_price = collection_data.collection.stats.floor

        payload = StickerPayload(
            gift_id=gift_id,
            price=floor_price,
            usd_price=floor_price * 1.4,
            stars_price=round(floor_price * 1.4 / 0.015),
            percent=(random.randint(0, 100) - 50) / 100,
        )

        await asyncio.sleep(sleep_for)
        await sticker_generator.generate_to_file(
            payload=payload, path=f"{GENERATIONS_PATH}/{name.replace(' ', '')}.png"
        )


async def main() -> None:
    args = parser.parse_args()

    if args.generate:
        log.debug("Generate")
        await generate()
    else:
        log.debug("Non generate")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.debug("Bye!")
