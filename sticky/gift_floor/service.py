from datetime import timedelta

from sqlalchemy import desc, func

from sticky.exceptions import ResourceNotFound
from sticky.gift.service import gift as gift_service
from sticky.gift_floor.repository import GiftFloorRepository
from sticky.kit.utils import utc_now
from sticky.models import Gift, GiftFloor
from sticky.postgres import AsyncSession
from sticky.thermos_proxy.client import ThermosProxy


class GiftFloorService:
    async def create(self, session: AsyncSession, floor: float, gift: Gift) -> GiftFloor:
        repository = GiftFloorRepository.from_session(session)
        return await repository.create(GiftFloor(floor=floor, gift=gift))

    async def get_latest(self, session: AsyncSession, gift: Gift) -> GiftFloor:
        repository = GiftFloorRepository.from_session(session)

        gift_floor = await repository.get_one_or_none(
            stmt=repository.get_base_stmt()
            .where(GiftFloor.gift == gift)
            .order_by(desc(GiftFloor.created_at))
        )

        if gift_floor is None:
            raise ResourceNotFound("Gift floors not found")

        return gift_floor

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

    async def update_from_thermos(
        self, session: AsyncSession, thermos_proxy: ThermosProxy
    ) -> None:
        collections = await thermos_proxy.get_collections()
        repository = GiftFloorRepository.from_session(session)

        for collection in collections:
            try:
                gift = await gift_service.get_by_telegram_id(
                    session, telegram_id=collection.id
                )
            except ResourceNotFound:
                gift = await gift_service.create(
                    session, name=collection.name, telegram_id=collection.id
                )

            await repository.create(GiftFloor(floor=collection.stats.floor, gift=gift))


gift_floor = GiftFloorService()
