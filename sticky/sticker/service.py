from collections.abc import Sequence

from sticky.models import Sticker
from sticky.postgres import AsyncSession


class StickerService:
    async def get_all(self, session: AsyncSession) -> Sequence[Sticker]:
        return []


sticker = StickerService()
