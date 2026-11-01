from datetime import timedelta

import pytest
from sqlalchemy import select

from sticky.exceptions import StickyError
from sticky.gift.service import gift as gift_service
from sticky.kit.utils import utc_now
from sticky.models import Gift, GiftFloor, Sticker
from sticky.postgres import AsyncSession
from tests.fixtures.database import SaveFixture
from tests.fixtures.random_objects import create_gift


async def create_gift_with_floor(save_fixture: SaveFixture, floor: float) -> Gift:
    gift = await create_gift(save_fixture)
    await save_fixture(GiftFloor(gift=gift, floor=floor))
    return gift


@pytest.mark.asyncio
async def test_get_all_sorts_by_latest_floor_and_skips_non_positive(
    session: AsyncSession, save_fixture: SaveFixture
) -> None:
    cheap = await create_gift_with_floor(save_fixture, floor=1)
    expensive = await create_gift_with_floor(save_fixture, floor=5)
    await create_gift_with_floor(save_fixture, floor=0)
    await create_gift(save_fixture)  # has no floors at all

    # Only the latest floor counts, this older floor would make it the top gift
    await save_fixture(
        GiftFloor(gift=cheap, floor=100, created_at=utc_now() - timedelta(days=1))
    )

    assert await gift_service.get_all(session) == [expensive, cheap]


@pytest.mark.asyncio
async def test_get_all_limit_keeps_highest_floors(
    session: AsyncSession, save_fixture: SaveFixture
) -> None:
    await create_gift_with_floor(save_fixture, floor=1)
    expensive = await create_gift_with_floor(save_fixture, floor=5)

    assert await gift_service.get_all(session, limit=1) == [expensive]


@pytest.mark.asyncio
async def test_deleting_gift_removes_its_floors_and_sticker(
    session: AsyncSession, save_fixture: SaveFixture
) -> None:
    gift = await create_gift_with_floor(save_fixture, floor=1)
    await save_fixture(Sticker(gift=gift, file="SomeFilePath", emojis="🎁"))

    await session.delete(gift)
    await session.flush()

    assert (await session.scalars(select(GiftFloor))).all() == []
    assert (await session.scalars(select(Sticker))).all() == []


@pytest.mark.asyncio
async def test_create_creates(session: AsyncSession) -> None:
    gift = await gift_service.create(session, name="Signet Ring", telegram_id="19129")

    assert gift is not None
    assert gift.name == "Signet Ring"
    assert gift.telegram_id == "19129"


@pytest.mark.asyncio
async def test_create_raises_if_duplicate_telegram_id(session: AsyncSession) -> None:
    await gift_service.create(session, name="Signet Ring", telegram_id="99999")

    with pytest.raises(StickyError):
        await gift_service.create(session, name="Diffie Name", telegram_id="99999")
