import random

import pytest_asyncio

from sticky.models import Gift
from tests.fixtures.database import SaveFixture


@pytest_asyncio.fixture
async def gift(save_fixture: SaveFixture) -> Gift:
    return await create_gift(save_fixture)


async def create_gift(
    save_fixture: SaveFixture, *, telegram_id: str | None = None
) -> Gift:
    if telegram_id is None:
        telegram_id = str(random.randint(1, 999999999999999999))

    gift = Gift(name="Signet Ring", telegram_id=telegram_id)
    await save_fixture(gift)
    return gift
