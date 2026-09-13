from collections.abc import Sequence

from sticky.exceptions import ResourceNotFound, StickyError
from sticky.gift.repository import GiftRepository
from sticky.models import Gift
from sticky.postgres import AsyncSession


class GiftService:
    async def get_all(self, session: AsyncSession) -> Sequence[Gift]:
        repository = GiftRepository.from_session(session)
        return await repository.get_all(stmt=repository.get_base_stmt())

    async def create(self, session: AsyncSession, name: str, telegram_id: str) -> Gift:
        repository = GiftRepository.from_session(session)
        gift = await repository.get_by_telegram_id_or_none(telegram_id=telegram_id)

        if gift is not None:
            raise StickyError()

        return await repository.create(
            Gift(name=name, telegram_id=telegram_id), flush=True
        )

    async def get_by_telegram_id(self, session: AsyncSession, telegram_id: str) -> Gift:
        repository = GiftRepository.from_session(session)
        gift = await repository.get_by_telegram_id_or_none(telegram_id=telegram_id)

        if gift is None:
            raise ResourceNotFound("Gift is not found")

        return gift


gift = GiftService()
