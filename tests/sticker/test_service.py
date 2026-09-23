import pytest
import pytest_asyncio

from sticky.models import Gift, Sticker
from sticky.sticker.service import sticker as sticker_service
from tests.fixtures.database import SaveFixture


@pytest_asyncio.fixture
async def sticker(save_fixture: SaveFixture, gift: Gift) -> Sticker:
    return await create_sticker(save_fixture, gift=gift)


async def create_sticker(
    save_fixture: SaveFixture, *, gift: Gift, emojis: list[str] | None = None
) -> Sticker:
    sticker = Sticker(
        gift=gift, file="SomeFilePath", emojis="🎁" if emojis is None else "".join(emojis)
    )
    await save_fixture(sticker)
    return sticker


def test_get_telegram_input_sticker_right_data(sticker: Sticker) -> None:
    input_sticker = sticker_service.get_telegram_input_sticker(sticker)

    assert input_sticker.emoji_list == sticker.emojis.split()


@pytest.mark.asyncio
async def test_get_telegram_input_empty_sticker_emojis_then_uses_default_emoji(
    save_fixture: SaveFixture, gift: Gift
) -> None:
    sticker = await create_sticker(save_fixture, gift=gift, emojis=[])
    input_sticker = sticker_service.get_telegram_input_sticker(sticker=sticker)

    assert input_sticker.emoji_list == ["🍊"]


# TODO: in future, when gift.emoji that is taken from gchanges or somewhere
# @pytest.mark.asyncio
# async def test_create_inherits_emoji_from_gift() -> None:
#     pass
