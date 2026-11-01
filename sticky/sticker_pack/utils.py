import asyncio

import structlog
from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramNotFound,
    TelegramRetryAfter,
)
from aiogram.types import Sticker as TelegramSticker

from sticky.config import settings
from sticky.exceptions import ResourceNotFound, StickyError
from sticky.gift.service import gift as gift_service
from sticky.gift_floor.service import gift_floor as gift_floor_service
from sticky.logging import Logger
from sticky.models import Gift, Sticker
from sticky.postgres import AsyncSession
from sticky.sticker.service import sticker as sticker_service
from sticky.sticker.utils import MAX_GIFT_STICKERS
from sticky.sticker_pack.service import sticker_pack as sticker_pack_service
from sticky.sticker_renderer import renderer as sticker_renderer

log: Logger = structlog.get_logger()


async def ensure_sticker_pack_is_created(session: AsyncSession, bot: Bot) -> None:
    """Ensures sticker pack is created on telegram side"""

    try:
        sticker_pack = await sticker_pack_service.get(session)

        if sticker_pack:
            try:
                sticker_set = await bot.get_sticker_set(name=settings.STICKER_PACK_NAME)
            except TelegramNotFound:
                await sticker_pack_service.create_in_telegram(bot)
            except TelegramBadRequest as exc:
                # Telegram reports a missing sticker set as this 400
                if "STICKERSET_INVALID" not in exc.message:
                    raise

                await sticker_pack_service.create_in_telegram(bot)
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

        created = await sticker_pack_service.create_in_telegram(bot)
        if created:
            sticker_pack = await sticker_pack_service.create(session)
            log.info("Created a new sticker pack", link=sticker_pack.link)


TG_RATE_LIMIT_SLEEP = 0.25


async def update_sticker_pack_in_telegram(session: AsyncSession, bot: Bot) -> None:
    """
    Publishes stickers to telegram,
    via getting all sticker records and editing to the fresh ones
    """

    gifts = await gift_service.get_all(
        session, only_positive_floor=True, limit=MAX_GIFT_STICKERS
    )
    sticker_set = await bot.get_sticker_set(name=settings.STICKER_PACK_NAME)

    tg_stickerpack_size = len(sticker_set.stickers)
    failed_gifts_count = 0

    for i, gift in enumerate(gifts):
        telegram_sticker = None
        # i + 1, since need to skip initial sticker
        if tg_stickerpack_size > i + 1:
            telegram_sticker = sticker_set.stickers[i + 1]

        gift_floor = await gift_floor_service.get_latest(session, gift=gift)

        if gift_floor.floor <= 0:
            log.warning(
                "Skipped publishing/updating, since somehow gift floor floor is zero or negative",
                floor=gift_floor.floor,
            )
            continue

        try:
            await update_sticker_in_sticker_pack_in_telegram(
                session, bot=bot, gift=gift, pre_existing_tg_sticker=telegram_sticker
            )
        except TelegramRetryAfter as exc:
            # Every next request would fail too, the next scheduled run picks it up
            log.warning(
                "Stopped sticker pack update, Telegram rate limit was hit",
                retry_after=exc.retry_after,
            )
            return
        except (TelegramBadRequest, FileNotFoundError) as exc:
            # Only errors specific to this gift, others (network, auth, ...) fail the run.
            # File is missing if this gift has never been rendered successfully
            failed_gifts_count += 1
            log.warning(
                "Skipped publishing a gift, since it failed",
                gift_id=gift.telegram_id,
                exc_info=exc,
            )

        await asyncio.sleep(TG_RATE_LIMIT_SLEEP)

    # Every gift failing means something is wrong globally (e.g. wrong owner id)
    if gifts and failed_gifts_count == len(gifts):
        raise StickyError("Publishing failed for every gift")

    gifts_in_stickerpack_count = len(gifts) + 1
    if gifts_in_stickerpack_count >= tg_stickerpack_size:
        return

    for i in range(gifts_in_stickerpack_count, tg_stickerpack_size):
        telegram_sticker = sticker_set.stickers[i]

        try:
            await telegram_sticker.delete_from_set()
        except TelegramRetryAfter as exc:
            log.warning(
                "Stopped sticker pack cleanup, Telegram rate limit was hit",
                retry_after=exc.retry_after,
            )
            return
        except TelegramBadRequest as exc:
            log.warning("Failed to delete a leftover sticker", exc_info=exc)

        await asyncio.sleep(TG_RATE_LIMIT_SLEEP)


async def update_sticker_in_sticker_pack_in_telegram(
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
