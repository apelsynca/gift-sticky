import structlog
from aiogram import Bot
from aiogram.types import FSInputFile, InputSticker
from sqlalchemy import select

from sticky.config import settings
from sticky.exceptions import ResourceNotFound, StickyError
from sticky.logging import Logger
from sticky.models import StickerPack
from sticky.postgres import AsyncSession


async def get_sticker_pack(session: AsyncSession) -> StickerPack:
    sticker_pack = await session.scalar(select(StickerPack))

    if sticker_pack is None:
        raise ResourceNotFound("Sticker pack is not created yet!")

    return sticker_pack


async def create_sticker_pack(session: AsyncSession) -> StickerPack:
    sticker_pack = await session.scalar(select(StickerPack))

    if sticker_pack is not None:
        raise StickyError("Sticker pack already exists")

    sticker_pack = StickerPack(name=settings.STICKER_PACK_NAME)

    session.add(sticker_pack)
    await session.flush()

    return sticker_pack


INITIAL_STICKERS = [
    InputSticker(
        sticker=FSInputFile("assets/initial_sticker.png"),
        format="static",
        emoji_list=["🍊"],
    )
]

log: Logger = structlog.get_logger()


async def ensure_sticker_pack_is_created(session: AsyncSession, bot: Bot) -> None:
    """Ensures sticker pack is created on telegram side"""

    try:
        await get_sticker_pack(session)
    except ResourceNotFound:
        created = await bot.create_new_sticker_set(
            user_id=settings.STICKER_PACK_OWNER_ID,
            name=settings.STICKER_PACK_NAME,
            title=settings.STICKER_PACK_TITLE,
            stickers=INITIAL_STICKERS,
        )
        if created:
            sticker_pack = await create_sticker_pack(session)
            log.info("Created a new sticker pack", link=sticker_pack.link)


async def update_sticker_pack_in_telegram(bot: Bot) -> None:
    """
    Publishes stickers to telegram,
    via getting all sticker records and editing to the fresh ones
    """
