import argparse

import structlog

from sticky.logging import Logger

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


def main() -> None:
    args = parser.parse_args()

    if args.generate:
        log.debug("Generate")
    else:
        log.debug("Non generate")


if __name__ == "__main__":
    main()
