from collections.abc import Sequence

from sqlalchemy import desc, func, select

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
    ) -> Sequence[Gift]:
        """
        Gets all Gift objects where:
        - ignore_as_sticker is False
        - latest GiftFloor related to Gift is > 0

        Also sorts by GiftFloor by default.
        """
        repository = GiftRepository.from_session(session)

        stmt = repository.get_base_stmt().where(Gift.ignore_as_sticker == False)

        needs_floor_join = only_positive_floor or sort_by_floor_desc
        if needs_floor_join:
            ranked_floors_subq = select(
                GiftFloor.gift_id.label("gift_id"),
                GiftFloor.floor.label("floor"),
                func.row_number()
                .over(
                    partition_by=GiftFloor.gift_id,
                    order_by=GiftFloor.created_at.desc(),
                )
                .label("rn"),
            ).subquery()
            latest_floors_subq = (
                select(
                    ranked_floors_subq.c.gift_id,
                    ranked_floors_subq.c.floor,
                )
                .where(ranked_floors_subq.c.rn == 1)
                .subquery()
            )

            stmt = stmt.outerjoin(
                latest_floors_subq, Gift.id == latest_floors_subq.c.gift_id
            )

            if only_positive_floor:
                stmt = stmt.where(latest_floors_subq.c.floor > 0)

            if sort_by_floor_desc:
                stmt = stmt.order_by(desc(latest_floors_subq.c.floor).nulls_last())

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
