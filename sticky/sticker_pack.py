from sqlalchemy import select

from sticky.config import settings
from sticky.exceptions import ResourceNotFound, StickyError
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
