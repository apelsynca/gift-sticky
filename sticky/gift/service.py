from sticky.exceptions import StickyError
from sticky.gift.repository import GiftRepository
from sticky.models import Gift
from sticky.postgres import AsyncSession


class GiftService:
    async def create(self, session: AsyncSession, name: str, telegram_id: str) -> Gift:
        repository = GiftRepository.from_session(session)

        gift = await repository.get_by_telegram_id_or_none(telegram_id=telegram_id)

        if gift is not None:
            raise StickyError()

        return await repository.create(
            Gift(name=name, telegram_id=telegram_id), flush=True
        )


gift = GiftService()
