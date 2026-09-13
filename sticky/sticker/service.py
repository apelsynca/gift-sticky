from aiogram.types import FSInputFile, InputSticker

from sticky.exceptions import ResourceNotFound
from sticky.models import Gift, Sticker
from sticky.postgres import AsyncSession
from sticky.sticker.repository import StickerRepository


class StickerService:
    async def get_by_gift(self, session: AsyncSession, gift: Gift) -> Sticker:
        repository = StickerRepository.from_session(session)
        sticker = await repository.get_one_or_none(
            stmt=repository.get_base_stmt().where(Sticker.gift == gift)
        )

        if sticker is None:
            raise ResourceNotFound("Sticker is not found")

        return sticker

    async def create(self, session: AsyncSession, gift: Gift, file: str) -> Sticker:
        repository = StickerRepository.from_session(session)

        emojis = "🎁"  # TODO: emoji based on gift itself (gift changes info maybe)

        return await repository.create(Sticker(gift=gift, file=file, emojis=emojis))

    def get_telegram_input_sticker(self, sticker: Sticker) -> InputSticker:
        return InputSticker(
            sticker=FSInputFile(sticker.file),
            format="static",
            emoji_list=list(sticker.emojis),
        )


sticker = StickerService()
