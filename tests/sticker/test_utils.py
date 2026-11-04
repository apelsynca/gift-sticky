from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from sticky.converter import Rates, TonConverter
from sticky.exceptions import StickyError
from sticky.models import GiftFloor
from sticky.postgres import AsyncSession
from sticky.sticker.utils import render_stickers
from tests.fixtures.database import SaveFixture
from tests.fixtures.random_objects import create_gift


@pytest.fixture
def converter_factory(mocker: MockerFixture) -> SimpleNamespace:
    converter = TonConverter.__new__(TonConverter)
    converter.set_rates(Rates(ton_usd=3.0))

    context = mocker.MagicMock()
    context.__aenter__ = AsyncMock(return_value=converter)
    context.__aexit__ = AsyncMock(return_value=False)

    return mocker.patch("sticky.sticker.utils.ton_converter", return_value=context)


@pytest.mark.asyncio
async def test_render_shares_converter_and_survives_a_failed_gift(
    session: AsyncSession,
    save_fixture: SaveFixture,
    mocker: MockerFixture,
    converter_factory: SimpleNamespace,
) -> None:
    price_time = datetime(2026, 9, 12, 10, 0, tzinfo=UTC)
    for floor in (3, 2, 1):
        gift = await create_gift(save_fixture)
        await save_fixture(GiftFloor(gift=gift, floor=floor, created_at=price_time))

    render = mocker.patch(
        "sticky.sticker.utils.sticker_renderer.render_and_save_to_file",
        new_callable=AsyncMock,
        side_effect=[ValueError("bad image"), None, None],
    )

    await render_stickers(session)

    converter_factory.assert_called_once()
    assert render.await_count == 3


@pytest.mark.asyncio
@pytest.mark.usefixtures("converter_factory")
async def test_render_raises_if_every_gift_failed(
    session: AsyncSession, save_fixture: SaveFixture, mocker: MockerFixture
) -> None:
    gift = await create_gift(save_fixture)
    await save_fixture(GiftFloor(gift=gift, floor=1))
    mocker.patch(
        "sticky.sticker.utils.sticker_renderer.render_and_save_to_file",
        new_callable=AsyncMock,
        side_effect=PermissionError("generations is not writable"),
    )

    with pytest.raises(StickyError):
        await render_stickers(session)
