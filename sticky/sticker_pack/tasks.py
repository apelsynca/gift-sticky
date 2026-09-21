import structlog
from litestar_queues import task

from sticky.logging import Logger

log: Logger = structlog.get_logger()


@task("sticker_pack.update", cron="@hourly", timezone="UTC")
async def update_sticker_pack() -> str:
    log.info("Updating sticker pack")
    return "Some result of the update"


@task("sticker_pack.poop", cron="* * * * *", timezone="UTC")
async def poop_at_sticker_pack() -> None:
    log.info("Hey LEG!, im pooping here...")
