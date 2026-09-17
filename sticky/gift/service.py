from collections.abc import Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.orm import aliased

from sticky.exceptions import ResourceNotFound, StickyError
from sticky.gift.repository import GiftRepository
from sticky.gift.sorting import GiftSortProperty
from sticky.kit.sorting import Sorting
from sticky.models import Gift
from sticky.models.gift_floor import GiftFloor
from sticky.postgres import AsyncSession


class GiftService:
    async def get_all(
        self,
        session: AsyncSession,
        sorting: list[Sorting[GiftSortProperty]] | None = None,
    ) -> Sequence[Gift]:
        if sorting is None:
            sorting = [(GiftSortProperty.floor, True)]

        repository = GiftRepository.from_session(session)

        stmt = repository.get_base_stmt()

        for property, is_desc in sorting:
            if property == GiftSortProperty.floor:
                ranked_floors_subq = select(
                    GiftFloor,
                    func.row_number()
                    .over(
                        partition_by=GiftFloor.gift_id,
                        order_by=GiftFloor.created_at.desc(),
                    )
                    .label("rn"),
                ).subquery()
                latest_floors = aliased(GiftFloor, ranked_floors_subq)

                stmt = stmt.outerjoin(latest_floors).order_by(
                    desc(latest_floors.floor).nulls_last()
                )

        return await repository.get_all(stmt=stmt)

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
