import pytest

from sticky.exceptions import StickyError
from sticky.gift.service import gift as gift_service
from sticky.postgres import AsyncSession


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
