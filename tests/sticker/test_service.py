import pytest

from sticky.postgres import AsyncSession
from sticky.sticker.service import sticker as sticker_service


@pytest.mark.asyncio
async def test_abc(session: AsyncSession) -> None:
    await sticker_service.get_all(session)
