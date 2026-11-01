from datetime import datetime
from typing import NamedTuple

from pydantic import BaseModel

from sticky.sticker_renderer.enums import StickerTypes


class GiftImageSettings(NamedTuple):
    """Settings for the gift image (size only for now)"""

    size: int

    @property
    def box_size(self) -> tuple[int, int]:
        return self.size, self.size


class StickerPayload(BaseModel):
    """
    Basically all of the info about sticker

    percent - Price change in percent
    *gift_id - Telegram gift ID
    *price - Current price in GRAM
    *usd_price - Current price in USD
    *stars_price - Current price in stars
    *price_updated_at - When the price was last recorded
    sticker_type -> type of the sticker based on percent
    """

    percent: float = 0
    gift_id: str
    price: float
    usd_price: float
    stars_price: int
    price_updated_at: datetime

    @property
    def sticker_type(self) -> StickerTypes:
        if self.percent == 0:
            return StickerTypes.neutral
        return StickerTypes.positive if self.percent > 0 else StickerTypes.negative

    def get_percent_sign(self) -> str:
        return "+" if self.percent > 0 else "-" if self.percent < 0 else ""
