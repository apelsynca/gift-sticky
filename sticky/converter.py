from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import timedelta

import structlog
from coingecko_sdk import AsyncCoingecko

from sticky.config import settings
from sticky.exceptions import StickyError
from sticky.logging import Logger
from sticky.redis import create_redis

log: Logger = structlog.get_logger()

USD_PER_STAR = 0.015


@dataclass
class Rates:
    """Snapshot of market rates, refreshed by whatever source feeds the converter."""

    ton_usd: float  # USD per 1 TON

    @property
    def ton_per_star(self) -> float:
        if self.ton_usd <= 0:
            return 0
        return USD_PER_STAR / self.ton_usd


class TonConverter:
    """
    Converts TON prices into USD and Telegram Stars prices,
    using the latest rates snapshot.

    Meant to replace raw rate math (e.g. `price * 1.4`)
    at the sticker payload call site (`sticky/sticker/utils.py`).
    """

    RATE_TTL = timedelta(minutes=180)
    REDIS_KEY = "STICKY_TON_RATE"

    def __init__(self, rates: Rates | None = None) -> None:
        self.redis = create_redis("app")
        self.coingecko = AsyncCoingecko(
            demo_api_key=settings.COINGECKO_DEMO_API_KEY, environment="demo"
        )
        self._rates: Rates | None = rates

    @property
    def rates(self) -> Rates:
        if self._rates is None:
            raise ValueError(
                f"Make sure you called `{self.__class__.__name__}.refresh_rates` "
                "at least once!"
            )
        return self._rates

    def set_rates(self, rates: Rates) -> None:
        """Updates the rates snapshot (e.g. after fetching fresh ones)."""
        self._rates = rates

    def to_usd(self, ton: float) -> float:
        """Converts TON amount into USD price using the current rates."""
        return self.rates.ton_usd * ton

    def to_stars(self, ton: float) -> int:
        """Converts TON amount into Telegram Stars price using the current rates."""
        return round(ton / self.rates.ton_per_star)

    async def refresh_rates(self) -> None:
        """Fetches fresh rates or gets cached and applies them onto the converter."""
        ton_usd = await self.redis.get(name=self.REDIS_KEY)

        if ton_usd is None:
            price_response = await self.coingecko.simple.price.get(
                vs_currencies="usd", ids="the-open-network"
            )
            ton_price = price_response.get("the-open-network")
            ton_usd = ton_price.usd if ton_price is not None else None

            if ton_usd is None or ton_usd <= 0:
                raise StickyError("CoinGecko returned no usable TON/USD rate")

            await self.redis.set(name=self.REDIS_KEY, value=ton_usd, ex=self.RATE_TTL)
        else:
            ton_usd = float(ton_usd)

        self.set_rates(rates=Rates(ton_usd=ton_usd))

    async def close(self) -> None:
        await self.redis.aclose()
        await self.coingecko.close()


@asynccontextmanager
async def ton_converter() -> AsyncGenerator[TonConverter]:
    """
    Yields a `TonConverter` with rates refreshed on enter.

    Usage:
        async with ton_converter() as converter:
            usd = converter.to_usd(1.5)
    """
    converter = TonConverter()

    try:
        await converter.refresh_rates()

        log.debug("Created ton converter", rates=converter.rates)

        yield converter
    finally:
        await converter.close()
