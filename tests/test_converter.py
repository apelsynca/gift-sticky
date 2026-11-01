from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from sticky.converter import TonConverter, ton_converter
from sticky.exceptions import StickyError


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.aclose = AsyncMock()

    async def get(self, name: str) -> str | None:
        return self.values.get(name)

    async def set(self, name: str, value: float, **_: object) -> None:
        self.values[name] = str(value)


@pytest.fixture
def redis(mocker: MockerFixture) -> FakeRedis:
    fake_redis = FakeRedis()
    mocker.patch("sticky.converter.create_redis", return_value=fake_redis)
    return fake_redis


@pytest.fixture
def coingecko(mocker: MockerFixture) -> AsyncMock:
    client = AsyncMock()
    client.simple.price.get.return_value = {"the-open-network": SimpleNamespace(usd=3.0)}
    mocker.patch("sticky.converter.AsyncCoingecko", return_value=client)
    return client


@pytest.mark.asyncio
@pytest.mark.usefixtures("redis")
async def test_second_refresh_uses_cached_rate(coingecko: AsyncMock) -> None:
    converter = TonConverter()

    await converter.refresh_rates()
    await converter.refresh_rates()

    coingecko.simple.price.get.assert_awaited_once()
    assert converter.rates.ton_usd == 3.0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response", [{}, {"the-open-network": SimpleNamespace(usd=None)}]
)
async def test_refresh_raises_and_caches_nothing_if_no_rate(
    redis: FakeRedis, coingecko: AsyncMock, response: dict
) -> None:
    coingecko.simple.price.get.return_value = response

    with pytest.raises(StickyError):
        await TonConverter().refresh_rates()

    assert redis.values == {}


@pytest.mark.asyncio
async def test_context_manager_closes_clients_even_if_refresh_fails(
    redis: FakeRedis, coingecko: AsyncMock
) -> None:
    coingecko.simple.price.get.return_value = {}

    with pytest.raises(StickyError):
        async with ton_converter():
            pass

    redis.aclose.assert_awaited_once()
    coingecko.close.assert_awaited_once()
