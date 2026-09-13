from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from sqlalchemy import select

from sticky.gift_floor.service import gift_floor as gift_floor_service
from sticky.kit.utils import utc_now
from sticky.models import Gift, GiftFloor
from sticky.postgres import AsyncSession
from sticky.thermos_proxy.client import ThermosProxy
from sticky.thermos_proxy.types import AggregatedStats, GiftCollection
from tests.fixtures.database import SaveFixture
from tests.fixtures.random_objects import create_gift


async def create_gift_floor(
    save_fixture: SaveFixture,
    *,
    floor: float,
    gift: Gift,
    deduct_creation: timedelta | None = None,
) -> GiftFloor:
    created_at = utc_now()
    if deduct_creation is not None:
        created_at -= deduct_creation

    gift_floor = GiftFloor(floor=floor, gift=gift, created_at=created_at)
    await save_fixture(gift_floor)
    return gift_floor


@pytest.mark.asyncio
async def test_get_floor_changes_zero_change_if_no_records(
    session: AsyncSession, gift: Gift
) -> None:
    floor_change = await gift_floor_service.get_floor_change(session, gift=gift)

    assert floor_change == 0  # 0%


@pytest.mark.asyncio
async def test_get_floor_changes_zero_change_if_different_gift(
    session: AsyncSession, save_fixture: SaveFixture, gift: Gift
) -> None:
    gift_second = await create_gift(save_fixture)
    await create_gift_floor(save_fixture, floor=1, gift=gift_second)
    await create_gift_floor(
        save_fixture, floor=2, gift=gift_second, deduct_creation=timedelta(days=1)
    )

    floor_change = await gift_floor_service.get_floor_change(session, gift=gift)

    assert floor_change == 0  # 0%


@freeze_time("2026-09-12 14:35:20")
@pytest.mark.asyncio
async def test_get_floor_changes_zero_change_if_no_records_till_yesterday(
    session: AsyncSession, save_fixture: SaveFixture, gift: Gift
) -> None:
    await create_gift_floor(save_fixture, floor=1.105, gift=gift)
    await create_gift_floor(
        save_fixture, floor=1.2, gift=gift, deduct_creation=timedelta(hours=2)
    )

    floor_change = await gift_floor_service.get_floor_change(session, gift=gift)

    assert floor_change == 0


@freeze_time("2026-09-12 12:00:00")
@pytest.mark.asyncio
async def test_get_floor_changes_right_change_amount(
    session: AsyncSession, save_fixture: SaveFixture, gift: Gift
) -> None:
    await create_gift_floor(save_fixture, floor=1, gift=gift)
    await create_gift_floor(
        save_fixture, floor=1.22, gift=gift, deduct_creation=timedelta(hours=1)
    )
    await create_gift_floor(
        save_fixture, floor=2.55, gift=gift, deduct_creation=timedelta(days=1, hours=2)
    )
    await create_gift_floor(
        save_fixture, floor=2, gift=gift, deduct_creation=timedelta(days=1)
    )

    floor_change = await gift_floor_service.get_floor_change(session, gift=gift)

    # -50% (2 -> 1), not (2.55 -> 1 since 2 was last entry yesterday)
    assert floor_change == -0.5


@pytest.mark.asyncio
async def test_create_creates(session: AsyncSession, gift: Gift) -> None:
    gift_floor = await gift_floor_service.create(session, floor=2.25, gift=gift)

    assert gift_floor is not None
    assert gift_floor.floor == 2.25


@pytest.mark.asyncio
async def test_fetch_latest_creates_right(session: AsyncSession, gift: Gift) -> None:
    thermos_proxy_mock = MagicMock(spec=ThermosProxy)
    gift_collection = GiftCollection(
        name="Can be any",
        image_url="https://can-be.any",
        stats=AggregatedStats(count=0, floor=1.23 * 1_000_000_000),
        id=gift.telegram_id,
    )
    thermos_proxy_mock.get_collections.return_value = [gift_collection]

    await gift_floor_service.update_from_thermos(session, thermos_proxy_mock)

    result = await session.scalars(select(GiftFloor))
    floors = result.all()
    assert len(floors) == 1
    assert floors[0].gift == gift
    assert floors[0].floor == 1.23
