import argparse
import asyncio

import structlog
from gchanges import GiftChanges

from sticky.logging import Logger
from sticky.sticker_generator import StickerPayload
from sticky.sticker_generator import generator as sticker_generator

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


async def generate() -> None:
    gift_changes = GiftChanges()

    names = await gift_changes.get_names()

    # for _, id in list(names.items())[:1]:

    gem_signet_id = "5859442703032386168"
    payload = StickerPayload(
        gift_id=gem_signet_id,
        price=12.2,
        usd_price=12.3,
        stars_price=515,
        percent=1.25,
    )

    await sticker_generator.generate(payload=payload)


async def main() -> None:
    args = parser.parse_args()

    if args.generate:
        log.debug("Generate")
        await generate()
    else:
        log.debug("Non generate")


if __name__ == "__main__":
    asyncio.run(main())
