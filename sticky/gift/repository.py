from sticky.kit.repository.main import BaseRepository
from sticky.models import Gift


class GiftRepository(BaseRepository[Gift]):
    model = Gift

    async def get_by_telegram_id_or_none(self, telegram_id: str) -> Gift | None:
        return await self.get_one_or_none(
            self.get_base_stmt().where(self.model.telegram_id == telegram_id)
        )
