import argparse
import asyncio

import structlog

from sticky.logging import Logger
from sticky.runner import generate_stickers, sticky_job_runner

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


async def run() -> None:
    args = parser.parse_args()

    if args.generate:
        await generate_stickers()
    else:
        await sticky_job_runner()


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        log.debug("Bye!")


if __name__ == "__main__":
    main()
