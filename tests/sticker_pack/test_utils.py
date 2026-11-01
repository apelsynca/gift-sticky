from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from aiogram.methods import GetStickerSet
from pytest_mock import MockerFixture

from sticky.exceptions import StickyError
from sticky.models import Gift, GiftFloor, StickerPack
from sticky.postgres import AsyncSession
from sticky.sticker_pack.utils import (
    ensure_sticker_pack_is_created,
    update_sticker_pack_in_telegram,
)
from tests.fixtures.database import SaveFixture
from tests.fixtures.random_objects import create_gift

METHOD = GetStickerSet(name="irrelevant")


def make_bot(stickers_in_pack: int) -> MagicMock:
    bot = MagicMock()
    stickers = [
        SimpleNamespace(file_id=str(i), delete_from_set=AsyncMock())
        for i in range(stickers_in_pack)
    ]
    bot.get_sticker_set = AsyncMock(return_value=SimpleNamespace(stickers=stickers))
    bot.add_sticker_to_set = AsyncMock(return_value=True)
    bot.replace_sticker_in_set = AsyncMock(return_value=True)
    return bot


async def create_gifts(save_fixture: SaveFixture, count: int) -> list[Gift]:
    gifts = []
    for floor in range(count, 0, -1):  # first gift is the most expensive one
        gift = await create_gift(save_fixture)
        await save_fixture(GiftFloor(gift=gift, floor=floor))
        gifts.append(gift)
    return gifts


@pytest.fixture(autouse=True)
def no_sleep(mocker: MockerFixture) -> None:
    mocker.patch("sticky.sticker_pack.utils.TG_RATE_LIMIT_SLEEP", 0)


@pytest.mark.asyncio
async def test_update_publishes_at_most_telegram_limit(
    session: AsyncSession, save_fixture: SaveFixture, mocker: MockerFixture
) -> None:
    await create_gifts(save_fixture, 3)
    mocker.patch("sticky.sticker_pack.utils.MAX_GIFT_STICKERS", 2)
    bot = make_bot(stickers_in_pack=1)

    await update_sticker_pack_in_telegram(session, bot)

    assert bot.add_sticker_to_set.await_count == 2


@pytest.mark.asyncio
async def test_update_continues_after_a_failed_gift(
    session: AsyncSession, save_fixture: SaveFixture
) -> None:
    await create_gifts(save_fixture, 3)
    bot = make_bot(stickers_in_pack=1)
    bot.add_sticker_to_set.side_effect = [
        TelegramBadRequest(METHOD, "bad sticker"),
        FileNotFoundError("never rendered"),
        True,
    ]

    await update_sticker_pack_in_telegram(session, bot)

    assert bot.add_sticker_to_set.await_count == 3


@pytest.mark.asyncio
async def test_update_raises_if_every_gift_failed(
    session: AsyncSession, save_fixture: SaveFixture
) -> None:
    await create_gifts(save_fixture, 2)
    bot = make_bot(stickers_in_pack=1)
    bot.add_sticker_to_set.side_effect = TelegramBadRequest(METHOD, "wrong owner")

    with pytest.raises(StickyError):
        await update_sticker_pack_in_telegram(session, bot)


@pytest.mark.asyncio
async def test_update_does_not_swallow_network_errors(
    session: AsyncSession, save_fixture: SaveFixture
) -> None:
    await create_gifts(save_fixture, 2)
    bot = make_bot(stickers_in_pack=1)
    bot.add_sticker_to_set.side_effect = TelegramNetworkError(METHOD, "no network")

    with pytest.raises(TelegramNetworkError):
        await update_sticker_pack_in_telegram(session, bot)

    assert bot.add_sticker_to_set.await_count == 1


@pytest.mark.asyncio
async def test_update_stops_on_rate_limit(
    session: AsyncSession, save_fixture: SaveFixture
) -> None:
    await create_gifts(save_fixture, 3)
    bot = make_bot(stickers_in_pack=5)
    bot.replace_sticker_in_set.side_effect = TelegramRetryAfter(METHOD, "flood", 60)

    await update_sticker_pack_in_telegram(session, bot)

    assert bot.replace_sticker_in_set.await_count == 1


@pytest.mark.asyncio
async def test_update_removes_leftover_stickers(
    session: AsyncSession, save_fixture: SaveFixture
) -> None:
    await create_gifts(save_fixture, 1)
    bot = make_bot(stickers_in_pack=4)
    stickers = bot.get_sticker_set.return_value.stickers

    await update_sticker_pack_in_telegram(session, bot)

    stickers[0].delete_from_set.assert_not_awaited()
    stickers[1].delete_from_set.assert_not_awaited()
    stickers[2].delete_from_set.assert_awaited_once()
    stickers[3].delete_from_set.assert_awaited_once()


@pytest.mark.asyncio
async def test_ensure_recreates_pack_missing_from_telegram(
    session: AsyncSession, mocker: MockerFixture
) -> None:
    session.add(StickerPack(name="pack_by_bot"))
    await session.flush()
    bot = make_bot(stickers_in_pack=0)
    bot.get_sticker_set.side_effect = TelegramBadRequest(METHOD, "STICKERSET_INVALID")
    create_in_telegram = mocker.patch(
        "sticky.sticker_pack.utils.sticker_pack_service.create_in_telegram",
        new_callable=AsyncMock,
    )

    await ensure_sticker_pack_is_created(session, bot)

    create_in_telegram.assert_awaited_once_with(bot)


@pytest.mark.asyncio
async def test_ensure_does_not_recreate_pack_on_other_bad_requests(
    session: AsyncSession, mocker: MockerFixture
) -> None:
    session.add(StickerPack(name="pack_by_bot"))
    await session.flush()
    bot = make_bot(stickers_in_pack=0)
    bot.get_sticker_set.side_effect = TelegramBadRequest(METHOD, "something else")
    create_in_telegram = mocker.patch(
        "sticky.sticker_pack.utils.sticker_pack_service.create_in_telegram",
        new_callable=AsyncMock,
    )

    with pytest.raises(TelegramBadRequest):
        await ensure_sticker_pack_is_created(session, bot)

    create_in_telegram.assert_not_awaited()
