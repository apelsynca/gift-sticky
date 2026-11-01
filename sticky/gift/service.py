from collections.abc import Sequence

from sqlalchemy import desc, select

from sticky.exceptions import ResourceNotFound, StickyError
from sticky.gift.repository import GiftRepository
from sticky.models import Gift, GiftFloor
from sticky.postgres import AsyncSession


class GiftService:
    async def get_all(
        self,
        session: AsyncSession,
        *,
        sort_by_floor_desc: bool = True,
        only_positive_floor: bool = True,
        limit: int | None = None,
    ) -> Sequence[Gift]:
        """
        Gets all Gift objects where:
        - ignore_as_sticker is False
        - latest GiftFloor related to Gift is > 0

        Also sorts by GiftFloor by default.
        Ties are broken by id, so that repeated limited calls return the same gifts.
        """
        repository = GiftRepository.from_session(session)

        stmt = repository.get_base_stmt().where(Gift.ignore_as_sticker == False)

        latest_floor = (
            select(GiftFloor.floor)
            .where(GiftFloor.gift_id == Gift.id)
            .order_by(GiftFloor.created_at.desc())
            .limit(1)
            .correlate(Gift)
            .scalar_subquery()
        )

        if only_positive_floor:
            stmt = stmt.where(latest_floor > 0)

        if sort_by_floor_desc:
            stmt = stmt.order_by(desc(latest_floor).nulls_last())

        stmt = stmt.order_by(Gift.id)

        if limit is not None:
            stmt = stmt.limit(limit)

        return await repository.get_all(stmt=stmt)

    async def create(self, session: AsyncSession, name: str, telegram_id: str) -> Gift:
        repository = GiftRepository.from_session(session)
        gift = await repository.get_by_telegram_id_or_none(telegram_id=telegram_id)

        if gift is not None:
            raise StickyError("Gift with that telegram_id already exists")

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
