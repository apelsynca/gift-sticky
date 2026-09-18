import asyncio

import structlog
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramNotFound
from aiogram.types import FSInputFile, InputSticker
from aiogram.types import Sticker as TelegramSticker
from sqlalchemy import select

from sticky.config import settings
from sticky.exceptions import ResourceNotFound, StickyError
from sticky.gift.service import gift as gift_service
from sticky.logging import Logger
from sticky.models import Gift, Sticker, StickerPack
from sticky.postgres import AsyncSession
from sticky.sticker.service import sticker as sticker_service
from sticky.sticker_renderer import renderer as sticker_renderer


async def get_sticker_pack(session: AsyncSession) -> StickerPack:
    sticker_pack = await session.scalar(select(StickerPack))

    if sticker_pack is None:
        raise ResourceNotFound("Sticker pack is not created yet!")

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
        sticker_pack = await get_sticker_pack(session)

        if sticker_pack:
            try:
                sticker_set = await bot.get_sticker_set(name=settings.STICKER_PACK_NAME)
            except TelegramNotFound:
                await create_sticker_pack_in_telegram(bot)
    except ResourceNotFound:
        try:
            sticker_set = await bot.get_sticker_set(name=settings.STICKER_PACK_NAME)
        except TelegramBadRequest:
            pass
        else:
            log.info(
                "Sticker pack was already created",
                link=f"https://t.me/addstickers/{sticker_set.name}",
            )
            return

        created = await create_sticker_pack_in_telegram(bot)
        if created:
            sticker_pack = await create_sticker_pack(session)
            log.info("Created a new sticker pack", link=sticker_pack.link)


async def create_sticker_pack_in_telegram(bot: Bot) -> bool:
    return await bot.create_new_sticker_set(
        user_id=settings.STICKER_PACK_OWNER_ID,
        name=settings.STICKER_PACK_NAME,
        title=settings.STICKER_PACK_TITLE,
        stickers=INITIAL_STICKERS,
    )


async def create_sticker_pack(session: AsyncSession) -> StickerPack:
    sticker_pack = await session.scalar(select(StickerPack))

    if sticker_pack is not None:
        raise StickyError("Sticker pack already exists")

    sticker_pack = StickerPack(name=settings.STICKER_PACK_NAME)

    session.add(sticker_pack)
    await session.flush()

    return sticker_pack


TG_RATE_LIMIT_SLEEP = 0.25


async def update_sticker_pack_in_telegram(session: AsyncSession, bot: Bot) -> None:
    """
    Publishes stickers to telegram,
    via getting all sticker records and editing to the fresh ones
    """

    gifts = await gift_service.get_all(session)

    sticker_set = await bot.get_sticker_set(name=settings.STICKER_PACK_NAME)

    tg_stickerpack_size = len(sticker_set.stickers)
    for i, gift in enumerate(gifts):
        telegram_sticker = None
        # i + 1, since need to skip initial sticker
        if tg_stickerpack_size > i + 1:
            telegram_sticker = sticker_set.stickers[i + 1]

        await update_sticker_in_sticker_pack_telegram(
            session, bot=bot, gift=gift, pre_existing_tg_sticker=telegram_sticker
        )
        await asyncio.sleep(TG_RATE_LIMIT_SLEEP)

    gifts_in_stickerpack_count = len(gifts) + 1
    if gifts_in_stickerpack_count >= tg_stickerpack_size:
        return

    for i in range(gifts_in_stickerpack_count, tg_stickerpack_size):
        telegram_sticker = sticker_set.stickers[i]
        await telegram_sticker.delete_from_set()
        await asyncio.sleep(TG_RATE_LIMIT_SLEEP)


async def update_sticker_in_sticker_pack_telegram(
    session: AsyncSession,
    bot: Bot,
    gift: Gift,
    *,
    pre_existing_tg_sticker: TelegramSticker | None = None,
) -> None:
    """
    Get sticker in database, if does not exist -> create + create in telegram
    If exists -> update + update in telegram
    """

    try:
        sticker = await sticker_service.get_by_gift(session, gift=gift)
    except ResourceNotFound:
        sticker = await sticker_service.create(
            session, gift=gift, file=sticker_renderer.get_render_path(gift.telegram_id)
        )

    await add_or_replace_sticker_in_telegram(
        bot=bot, sticker=sticker, pre_existing_tg_sticker=pre_existing_tg_sticker
    )


async def add_or_replace_sticker_in_telegram(
    bot: Bot, sticker: Sticker, pre_existing_tg_sticker: TelegramSticker | None = None
) -> None:
    if pre_existing_tg_sticker is None:
        is_sticker_added = await bot.add_sticker_to_set(
            user_id=settings.STICKER_PACK_OWNER_ID,
            name=settings.STICKER_PACK_NAME,
            sticker=sticker_service.get_telegram_input_sticker(sticker),
        )

        log.info(
            "Requested to add a sticker to sticker pack",
            file=sticker.file,
            gift=sticker.gift,
            success=is_sticker_added,
        )

    else:
        is_stiker_replaced = await bot.replace_sticker_in_set(
            user_id=settings.STICKER_PACK_OWNER_ID,
            name=settings.STICKER_PACK_NAME,
            old_sticker=pre_existing_tg_sticker.file_id,
            sticker=sticker_service.get_telegram_input_sticker(sticker),
        )

        log.info(
            "Requested to replace a sticker to sticker pack",
            file=sticker.file,
            gift=sticker.gift,
            success=is_stiker_replaced,
        )
