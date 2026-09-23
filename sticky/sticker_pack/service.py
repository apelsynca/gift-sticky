from aiogram import Bot
from aiogram.types import FSInputFile, InputSticker
from sqlalchemy import select

from sticky.config import settings
from sticky.exceptions import ResourceNotFound, StickyError
from sticky.models import StickerPack
from sticky.postgres import AsyncSession

INITIAL_STICKER = InputSticker(
    sticker=FSInputFile("assets/initial_sticker.png"),
    format="static",
    emoji_list=["🍊"],
)


class StickerPackService:
    """
    Service to interact with anything sticker pack related

    StickerPack - Model in database containing single object,
    with stuff about whole Sticker Pack
    """

    async def get(self, session: AsyncSession) -> StickerPack:
        sticker_pack = await session.scalar(select(StickerPack))

        if sticker_pack is None:
            raise ResourceNotFound("Sticker pack is not created yet!")

        return sticker_pack

    async def create(self, session: AsyncSession) -> StickerPack:
        sticker_pack = await session.scalar(select(StickerPack))

        if sticker_pack is not None:
            raise StickyError("Sticker pack already exists")

        sticker_pack = StickerPack(name=settings.STICKER_PACK_NAME)

        session.add(sticker_pack)
        await session.flush()

        return sticker_pack

    async def create_in_telegram(self, bot: Bot) -> bool:
        """Returns boolean flag if created"""
        return await bot.create_new_sticker_set(
            user_id=settings.STICKER_PACK_OWNER_ID,
            name=settings.STICKER_PACK_NAME,
            title=settings.STICKER_PACK_TITLE,
            stickers=[INITIAL_STICKER],
        )


sticker_pack = StickerPackService()
