from datetime import timedelta

from sqlalchemy import desc, func

from sticky.gift_floor.repository import GiftFloorRepository
from sticky.kit.utils import utc_now
from sticky.models import Gift, GiftFloor
from sticky.postgres import AsyncSession


class GiftFloorService:
    async def create(self, session: AsyncSession, floor: float, gift: Gift) -> GiftFloor:
        repository = GiftFloorRepository.from_session(session)
        return await repository.create(GiftFloor(floor=floor, gift=gift))

    async def get_floor_change(self, session: AsyncSession, gift: Gift) -> float:
        repository = GiftFloorRepository.from_session(session)

        last_floor = await repository.get_one_or_none(
            stmt=repository.get_base_stmt()
            .where(
                GiftFloor.gift == gift,
                func.date(GiftFloor.created_at) == utc_now().date(),
            )
            .order_by(desc(GiftFloor.created_at))
        )
        if last_floor is None:
            return 0

        yesterday_floor = await repository.get_one_or_none(
            stmt=repository.get_base_stmt()
            .where(
                GiftFloor.gift == gift,
                func.date(GiftFloor.created_at) == (utc_now() - timedelta(days=1)).date(),
            )
            .order_by(desc(GiftFloor.created_at))
        )
        if yesterday_floor is None:
            return 0

        return (last_floor.floor - yesterday_floor.floor) / yesterday_floor.floor


gift_floor = GiftFloorService()
